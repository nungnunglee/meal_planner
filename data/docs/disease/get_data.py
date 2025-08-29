import os
import re
from lxml import etree
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI


# 이미지 및 비디오의 기본 URL (XML에 상대 경로로 되어 있으므로 필요)
BASE_URL = "https://chs.kdca.go.kr"


# 1. 이미지의 링크를 입력으로 받고 gemini로 이미지 설명을 만들어 문자열을 반환하는 함수
def generate_image_description(image_url: str) -> str:
    """
    주어진 이미지 URL에 대해 LangChain의 Google Gemini 모델을 사용하여 설명을 생성합니다.

    Args:
        image_url (str): 설명할 이미지의 URL.

    Returns:
        str: 생성된 이미지 설명. 오류 발생 시 빈 문자열을 반환합니다.
    """
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash") # gemini-pro-vision 모델 사용

        message = HumanMessage(
            content=[
                {"type": "text", "text": "이 이미지를 자세히 설명해 주세요."},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
        )

        response = llm.invoke([message])
        return response.content.strip()
    except Exception as e:
        print(f"Error generating image description for {image_url} using LangChain: {e}")
        return ""

# 2. xml 파일 경로, 저장 디렉토리 경로를 입력받아 .md 형식으로 변환하고 입력 파일 이름으로 저장 디렉토리에 저장
def convert_xml_to_md(xml_file_path: str, output_dir: str):
    """
    XML 파일을 파싱하고 이미지 링크에 대한 설명을 Gemini를 통해 생성하여
    Markdown 형식으로 변환한 후 지정된 디렉토리에 저장합니다.

    Args:
        xml_file_path (str): 변환할 XML 파일의 전체 경로.
        output_dir (str): 변환된 Markdown 파일을 저장할 디렉토리 경로.
    """
    if not os.path.exists(xml_file_path):
        print(f"Error: XML file not found at {xml_file_path}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    try:
        parser = etree.XMLParser(recover=True, encoding='utf-8') # CDATA와 잘못된 HTML 태그 처리를 위해 recover=True 추가
        tree = etree.parse(xml_file_path, parser)
        root = tree.getroot()

        md_content = []

        # 질병명 추출 (CNTNTSSJ 태그)
        disease_title_element = root.find('.//CNTNTSSJ')
        if disease_title_element is not None and disease_title_element.text:
            disease_title = disease_title_element.text.strip()
            md_content.append(f"# {disease_title}\n\n")
        else:
            # 제목을 찾지 못하면 파일 이름을 제목으로 사용
            disease_title = os.path.splitext(os.path.basename(xml_file_path))[0]
            md_content.append(f"# {disease_title}\n\n")

        # 각 cntntsCl 섹션 처리
        for cntnts_cl in root.findall('.//cntntsCl'):
            cl_name_element = cntnts_cl.find('CNTNTS_CL_NM')
            cl_content_element = cntnts_cl.find('CNTNTS_CL_CN')

            section_title = ""
            if cl_name_element is not None and cl_name_element.text:
                section_title = cl_name_element.text.strip()
                md_content.append(f"## {section_title}\n\n")

            if cl_content_element is not None and cl_content_element.text:
                raw_html_content = cl_content_element.text.strip()

                # HTML 태그 제거 및 Markdown 형식으로 변환
                # <p>, <ul>, <li>, <b>, <span>, <br> 등 처리
                # CDATA 섹션 내의 HTML을 파싱하기 위해 ElementTree를 한 번 더 사용
                try:
                    # CDATA 내부의 HTML을 파싱
                    html_parser = etree.HTMLParser()
                    html_tree = etree.fromstring(raw_html_content, html_parser)
                    
                    # Markdown으로 변환
                    section_text_parts = []
                    for node in html_tree.iter():
                        if node.tag == 'p' and node.text and node.text.strip():
                            section_text_parts.append(node.text.strip() + "\n\n")
                        elif node.tag == 'ul':
                            for li in node.findall('li'):
                                if li.text and li.text.strip():
                                    # <li> 내부의 <b>, <span> 등을 처리하기 위해 다시 한번 텍스트 정제
                                    list_item_text = etree.tostring(li, encoding='unicode', method='text').strip()
                                    section_text_parts.append(f"* {list_item_text}\n")
                            section_text_parts.append("\n") # 리스트 뒤에 줄바꿈 추가
                        elif node.tag == 'b' and node.text and node.text.strip():
                            section_text_parts.append(f"**{node.text.strip()}**")
                        elif node.tag == 'span' and node.text and node.text.strip():
                            # span 태그는 텍스트만 추출
                            section_text_parts.append(node.text.strip())
                        elif node.tag == 'br':
                            section_text_parts.append("\n") # <br> 태그는 줄바꿈으로
                        
                        # 이미지 태그 처리
                        if node.tag == 'img' and 'src' in node.attrib:
                            img_src = node.attrib['src']
                            # 상대 경로를 절대 경로로 변환
                            if img_src.startswith("/"):
                                full_image_url = BASE_URL + img_src
                            else:
                                full_image_url = img_src # 이미 절대 경로인 경우

                            print(f"Generating description for image: {full_image_url}")
                            description = generate_image_description(full_image_url)
                            if description:
                                md_content.append(f"### 이미지 설명\n") # 이미지 설명을 소소제목으로
                                md_content.append(f"> {description}\n\n") # 인용 블록으로 설명 추가
                            md_content.append(f"![{node.attrib.get('alt', '이미지')}]({full_image_url})\n\n") # 원본 이미지 링크 포함
                        
                        # 비디오 태그 처리 (src 속성을 가진 source 태그 찾기)
                        if node.tag == 'video':
                            source_element = node.find('source')
                            if source_element is not None and 'src' in source_element.attrib:
                                video_src = source_element.attrib['src']
                                # 상대 경로를 절대 경로로 변환
                                if video_src.startswith("/"):
                                    full_video_url = BASE_URL + video_src
                                else:
                                    full_video_url = video_src # 이미 절대 경로인 경우
                                
                                md_content.append(f"### 비디오\n")
                                md_content.append(f"[비디오 링크]({full_video_url})\n\n")
                                # 비디오 설명이 필요하다면 여기에 generate_video_description 같은 함수 호출
                                # 현재는 비디오 설명 생성 기능은 포함하지 않습니다.

                    # 최종 텍스트 콘텐츠 추가
                    section_text = "".join(section_text_parts).strip()
                    if section_text:
                        md_content.append(section_text + "\n\n")

                except etree.XMLSyntaxError as e:
                    # CDATA 내부의 HTML이 유효하지 않을 경우, 원본 텍스트에서 HTML 태그만 제거
                    print(f"Warning: Invalid HTML in CDATA for {section_title}. Attempting plain text extraction. Error: {e}")
                    clean_text = re.sub(r'<[^>]+>', '', raw_html_content) # 모든 HTML 태그 제거
                    md_content.append(clean_text.strip() + "\n\n")


        # Markdown 파일 저장
        output_filename = disease_title.replace(" ", "_") + ".md" # 파일명에 공백을 _로 대체
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("".join(md_content))
        print(f"Successfully converted '{xml_file_path}' to '{output_path}'")

    except etree.XMLSyntaxError as e:
        print(f"Error parsing XML file {xml_file_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during conversion: {e}")


def remove_xml_style_message(file_path: str) -> None:
    """
    XML 파일에서 "This XML file does not appear to have any style information associated with it." 
    메시지를 제거합니다.

    Args:
        file_path (str): 수정할 XML 파일의 경로
    """
    try:
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 해당 메시지 제거
        pattern = r'This XML file does not appear to have any style information associated with it\. The document tree is shown below\.\n'
        modified_content = re.sub(pattern, '', content)

        # 파일 다시 쓰기
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        print(f"Successfully removed style message from {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def process_all_xml_files(directory_path: str) -> None:
    """
    주어진 디렉토리 내의 모든 XML 파일에서 스타일 메시지를 제거합니다.

    Args:
        directory_path (str): XML 파일들이 있는 디렉토리 경로
    """
    try:
        # 디렉토리 내의 모든 XML 파일 처리
        for filename in os.listdir(directory_path):
            if filename.endswith('.xml'):
                file_path = os.path.join(directory_path, filename)
                remove_xml_style_message(file_path)
        
        print("All XML files have been processed")
    except Exception as e:
        print(f"Error processing directory {directory_path}: {e}")


if __name__ == "__main__":
    xml_file_path = "Agent/rag_doc/guidelines/disease/건강기능식품.xml"
    output_dir = "output"
    # convert_xml_to_md(xml_file_path, output_dir)
    files = os.listdir("Agent/rag_doc/guidelines/disease")
    for file in files:
        if file.endswith(".xml"):
            xml_file_path = os.path.join("Agent/rag_doc/guidelines/disease", file)
            print(xml_file_path)
            convert_xml_to_md(xml_file_path, output_dir)

    # # XML 파일 처리 예시
    # xml_directory = "Agent/rag_doc/guidelines/disease"
    # process_all_xml_files(xml_directory)