from tqdm import tqdm
from langchain_core.documents import Document
from Agent.qdrant_manager import QdrantManager, collections
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownTextSplitter
import pymupdf
import os


class FoodReader:
    @staticmethod
    def get_docs_from_food_name(food_name_path: str) -> list[Document]:
        documents = []
        with open(food_name_path, "r", encoding="utf-8") as f:
            for line in tqdm(f.readlines(), desc="Getting food name documents"):
                food_id, food_name = line.split(",", 1)
                documents.append(Document(page_content=food_name.strip(), metadata={"food_id": food_id.strip(), "food_name": food_name.strip()}))
        return documents
    
    @staticmethod
    def get_docs_from_food_tag(food_tag_path: str) -> list[Document]:
        documents = []
        with open(food_tag_path, "r", encoding="utf-8") as f:
            for line in tqdm(f.readlines(), desc="Getting food tag documents"):
                tag_id, tag_name = line.split(",", 1)
                documents.append(Document(page_content=tag_name.strip(), metadata={"tag_id": tag_id.strip(), "tag_name": tag_name.strip()}))
        return documents

class PdfReader:
    @staticmethod
    def get_docs_from_pdf(pdf_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[Document]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            is_separator_regex=False
        )

        documents = []
        with pymupdf.open(pdf_path) as doc:
            file_name = os.path.basename(pdf_path)
            for page_num in tqdm(range(doc.page_count), desc=f"document화 진행 중: {file_name}"):
                current_section = PdfReader.get_section_to_idx(doc, page_num+1)
                page = doc.load_page(page_num)
                text_docs = PdfReader.docs_from_texts(
                        texts=text_splitter.split_text(page.get_text()), 
                        metadata={
                            "source": file_name, 
                            "page": page_num+1, 
                            "type": "text", 
                            "section": current_section
                        }
                    )
                tables_docs = PdfReader.docs_from_tables(
                    tables=page.find_tables(), 
                    metadata={
                        "source": file_name, 
                        "page": page_num+1, 
                        "type": "table", 
                        "section": current_section
                    }
                )
                links_docs = PdfReader.docs_from_links(
                    links=page.find_links(), 
                    metadata={
                        "source": file_name, 
                        "page": page_num+1, 
                        "type": "link", 
                        "section": current_section
                    }
                )
                contents_docs = text_docs + tables_docs + links_docs
                documents.extend(contents_docs)
        return documents

    @staticmethod
    def get_section_to_idx(doc, page_num):
        toc = doc.get_toc()
        if not toc:
            return "N/A"
        if page_num < toc[0][2]:
            return "cover page"
        if page_num > doc.page_count:
            return "N/A"

        # 섹션 찾기
        last_section = toc[0][1]
        for i, (level, title, start_page_num) in enumerate(toc):
            if page_num < start_page_num:
                return last_section
            last_section = title
        return last_section  # 마지막 섹션 이후면 마지막 섹션 반환
    
    @staticmethod
    def docs_from_texts(texts: list[str], metadata: dict):
        contents_docs = []
        for text in texts:
            contents_docs.append(Document(
                page_content=text,
                metadata=metadata
            ))
        return contents_docs
    
    @staticmethod
    def docs_from_tables(tables: list[pymupdf.Table], metadata: dict):
        contents_docs = []
        for table in tables:
            contents_docs.append(Document(
                page_content=table.to_pandas().to_markdown(),
                metadata=metadata
            ))
        return contents_docs
    
    @staticmethod
    def docs_from_links(links: list[pymupdf.Link], metadata: dict):
        contents_docs = []
        for link in links:
            if link['kind'] == pymupdf.LINK_URI:
                contents_docs.append(Document(
                    page_content=f"페이지 {metadata['page']}에 외부 웹사이트 '{link['uri']}'로 연결되는 링크가 있습니다.",
                    metadata={**metadata, "link_url": link['uri']}
                ))
        return contents_docs
    
class GuidelinesReader:
    @staticmethod
    def get_docs_from_guidelines(guidelines_dir: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[Document]:
        documents = []
        markdown_splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for file in tqdm(list(guidelines_dir.glob("*.md")), desc="Getting guidelines documents"):
            with open(file, "r", encoding="utf-8") as f:
                texts = markdown_splitter.split_text(f.read())
                for i, text in enumerate(texts):
                    documents.append(Document(page_content=text, metadata={"source": file.name, "chunk_id": i}))
        return documents


class QdrantSetter:
    def __init__(self, pdf_paths: list[str], guidelines_dir: str, food_name_path: str, food_tag_path: str, batch_size: int = 1000):
        self.qdrant_manager = QdrantManager()
        self.batch_size = batch_size
        self.pdf_paths = pdf_paths
        self.guidelines_dir = guidelines_dir
        self.food_name_path = food_name_path
        self.food_tag_path = food_tag_path
    
    def set_all(self, reset: bool = False):
        if reset:
            print("Resetting qdrant")
            self.qdrant_manager.reset_collection(collections.food_docs_collection)
            self.qdrant_manager.reset_collection(collections.food_name_collection)
            self.qdrant_manager.reset_collection(collections.food_tag_collection)
        
        print("Setting documents to qdrant")
        self.set_pdf()
        self.set_guidelines()
        self.set_food_name()
        self.set_food_tag()

    def set_pdf(self):
        for i, pdf_path in enumerate(self.pdf_paths):
            print(f"Adding pdf documents to qdrant: {i+1}/{len(self.pdf_paths)} {pdf_path}")
            self.qdrant_manager.add_documents(
                documents=PdfReader.get_docs_from_pdf(pdf_path), 
                collection_name=collections.food_docs_collection, 
                batch_size=self.batch_size
            )

    def set_guidelines(self):
        print(f"Adding guidelines documents to qdrant: {self.guidelines_dir}")
        self.qdrant_manager.add_documents(
            documents=GuidelinesReader.get_docs_from_guidelines(self.guidelines_dir), 
            collection_name=collections.food_docs_collection, 
            batch_size=self.batch_size
        )

    def set_food_name(self):
        print(f"Adding food name documents to qdrant: {self.food_name_path}")
        self.qdrant_manager.add_documents(
            documents=FoodReader.get_docs_from_food_name(self.food_name_path), 
            collection_name=collections.food_name_collection, 
            batch_size=self.batch_size
        )

    def set_food_tag(self):
        print(f"Adding food tag documents to qdrant: {self.food_tag_path}")
        self.qdrant_manager.add_documents(
            documents=FoodReader.get_docs_from_food_tag(self.food_tag_path), 
            collection_name=collections.food_tag_collection, 
            batch_size=self.batch_size
        )

if __name__ == "__main__":
    qdrant_setter = QdrantSetter(
        pdf_paths=[
            "docs/nutrition/Nutrition-Science-and-Everyday-Application-1694655583.pdf", 
            "docs/nutrition/The Need for Professional Training in Nutrition Education and Communication_CASE STUDY REPORT.pdf",
            "docs/physiology/Essentials of Anatomy and Physiology ( PDFDrive ).pdf",
            "docs/physiology/Guyton and Hall Textbook of Medical Physiology ( PDFDrive ).pdf"
        ],
        guidelines_dir="guidelines/disease",
        food_name_path="food/foods_id_name.txt",
        food_tag_path="food/tags_id_name.txt"
    )
    qdrant_setter.set_all(reset=False)