from typing import TypedDict, Annotated, Dict, List
from langchain_core.runnables import RunnableConfig

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing import Sequence
from pydantic import BaseModel, Field
from Agent.prompts.prompt import recommender_prompt, plan_prompt
from Agent.tools.tools import (
    retriever_tool, format_nutrient_json, generate_weekly_meal_plan, 
    get_food_nutrient,
    WeeklyMealPlan, NutrientData
)

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI
import logging


logger = logging.getLogger(__name__)

config = RunnableConfig(recursion_limit=10)


class UserProfile(BaseModel):
    """
    사용자의 신체 및 건강, 식습관 정보를 담는 Pydantic 모델.
    """
    age: int = Field(..., description="사용자의 나이 (만 나이, 1세 이상 120세 이하)", ge=1, le=120)
    gender: str = Field(..., description="사용자의 성별 ('남성' 또는 '여성')")
    height: float = Field(..., description="사용자의 키 (cm, 50.0cm 이상 250.0cm 이하)", ge=50.0, le=250.0)
    weight: float = Field(..., description="사용자의 몸무게 (kg, 10.0kg 이상 300.0kg 이하)", ge=10.0, le=300.0)
    diseases: List[str] = Field(default_factory=list, description="사용자가 앓고 있는 질병 목록 (없으면 빈 리스트)")
    favorite_foods: List[str] = Field(default_factory=list, description="사용자가 좋아하는 음식 목록 (없으면 빈 리스트)")
    disliked_foods: List[str] = Field(default_factory=list, description="사용자가 싫어하는 음식 목록 (없으면 빈 리스트)")
    activity_level: str = Field(..., description="사용자의 활동 수준 (sedentary, lightly_exercising, moderately_exercising, heavy_exercising)")

    def to_dict(self) -> Dict:
        return {
            "age": self.age,
            "gender": self.gender,
            "height": self.height,
            "weight": self.weight,
            "diseases": ", ".join(self.diseases) if len(self.diseases) > 0 else "해당사항없음",
            "favorite_foods": ", ".join(self.favorite_foods) if len(self.favorite_foods) > 0 else "해당사항없음",
            "disliked_foods": ", ".join(self.disliked_foods) if len(self.disliked_foods) > 0 else "해당사항없음",
            "activity_level": self.activity_level,
        }


class ScheduleState(TypedDict):
    user_profile: Annotated[UserProfile, "user profile"] # 사용자 프로필 정보
    keywords: Annotated[str, "식단 유형(저탄고지/고단백/비건 등), 제한사항(알레르기/종교), 목표(체중감량/근육증가), 준비시간(간편식/정성식) 등의 식단 생성 관련 키워드"]
    recommender_messages: Annotated[Sequence[BaseMessage], add_messages] # 권장되는 영양성분 정보를 만들기 위해 recommender가 사용하는 메시지
    plan_messages: Annotated[Sequence[BaseMessage], add_messages] # 영양성분을 잘 맞춘 식단 정보를 만들기 위해 plan_generator가 사용하는 메시지
    nutrient_table: Annotated[NutrientData, "생성된 권장되는 영양성분 정보"]
    meal_table: Annotated[str, "생성된 식단 정보"]
    # nutrient_binary_score: Annotated[str, "binary score yes or no"] # 영양성분 정보가 잘 맞는지 확인하기 위해 사용하는 메시지
    # plan_binary_score: Annotated[str, "binary score yes or no"] # 식단 정보가 잘 맞는지 확인하기 위해 사용하는 메시지
    
    
class ScheduleAgent:
    def __init__(self):
        logger.info("initializing schedule agent")
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        self.recommender_tools = [retriever_tool, format_nutrient_json]
        self.plan_tools = [retriever_tool, generate_weekly_meal_plan, get_food_nutrient]
        self.workflow = StateGraph(ScheduleState)
        self.workflow.add_node("nutrient_recommender", self.nutrient_recommender)
        self.workflow.add_node("nutrient_recommender_tools", ToolNode(self.recommender_tools, messages_key="recommender_messages"))
        # self.workflow.add_node("nutrient_relevance_check", self.nutrient_relevance_check)
        self.workflow.add_node("set_nutrient_table", self.set_nutrient_table)
        self.workflow.add_node("meal_plan_generator", self.meal_plan_generator)
        self.workflow.add_node("set_meal_table", self.set_meal_table)
        self.workflow.add_node("meal_plan_generator_tools", ToolNode(self.plan_tools, messages_key="plan_messages"))
        # self.workflow.add_node("plan_relevance_check", self.plan_relevance_check)

        self.workflow.set_entry_point("nutrient_recommender")
        self.workflow.add_conditional_edges(
            source="nutrient_recommender",
            path=lambda state: "tools" if tools_condition(state, messages_key="recommender_messages") == "tools" else "next",
            path_map={
                "tools": "nutrient_recommender_tools",
                "next": "set_nutrient_table",
                # "next": "nutrient_relevance_check",
            },
        )
        self.workflow.add_edge("nutrient_recommender_tools", "nutrient_recommender")
        self.workflow.add_edge("set_nutrient_table", "meal_plan_generator")
        self.workflow.add_conditional_edges(
            source="meal_plan_generator",
            path=lambda state: "tools" if tools_condition(state, messages_key="plan_messages") == "tools" else "next",
            path_map={
                "tools": "meal_plan_generator_tools",
                "next": "set_meal_table",
                # "next": "plan_relevance_check",
            },
        )
        self.workflow.add_edge("meal_plan_generator_tools", "meal_plan_generator")
        self.workflow.add_edge("set_meal_table", END)

        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)
        logger.info("compiled workflow")
    
    def get_graph_image(self) -> bytes:
        return self.app.get_graph(xray=True).draw_mermaid_png()#draw_method=MermaidDrawMethod.API)

    def nutrient_recommender(self, state: ScheduleState) -> ScheduleState:
        model_with_tools = self.llm.bind_tools(self.recommender_tools)
        response = (recommender_prompt | model_with_tools).invoke({
            "recommender_messages": state["recommender_messages"], 
            "user_profile": state["user_profile"].to_dict()
            })
        return {"recommender_messages": [response]}
    
    def set_nutrient_table(self, state: ScheduleState) -> ScheduleState:
        nutrient_data = self.llm.with_structured_output(NutrientData).invoke(state["recommender_messages"][-1].content)
        return {"nutrient_table": nutrient_data.model_dump()}

    def meal_plan_generator(self, state: ScheduleState) -> ScheduleState:
        model_with_tools = self.llm.bind_tools(self.plan_tools)
        response = (plan_prompt | model_with_tools).invoke({
            "plan_messages": state["plan_messages"], 
            "user_profile": state["user_profile"].to_dict(),
            "keywords": state["keywords"],
            "nutrient_table": state["nutrient_table"]
            })
        return {"plan_messages": [response]}
    
    def set_meal_table(self, state: ScheduleState) -> ScheduleState:
        meal_data = self.llm.with_structured_output(WeeklyMealPlan).invoke(state["plan_messages"][-1].content)
        return {"meal_table": meal_data.model_dump()}    
        

schedule_agent = ScheduleAgent()
logger.info("created schedule agent")
        
"""
2015년 한국인 영양섭취기준

구분	에너지(kcal/일)	단백질(g/일)
남자	여자	남자	여자
1~2세	1000	15
3~5세	1400	20
6~8세	1700	1500	30	25
9~11세	2100	1800	40	40
12~14세	2500	2000	55	50
15~18세	2700	2000	65	50
19~29세	2600	2100	65	55
30~49세	2400	1900	60	50
50~64세	2200	1800	60	50
65~74세	2000	1600	55	45
75~120세	2000	1600	55	45
임신부/초기	+0	+0
임신부/중기	+340	+15
임신부/후기	+450	+30
수유부	+340	+25
용어해설서
필요추정량건강하고 정상적인 활동을 하며, 정상 체격을 지닌 사람이 에너지의 평형을 유지하는데 필요한 양

"""