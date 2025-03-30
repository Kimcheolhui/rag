# RAG 기반 영화 챗봇

Azure OpenAI와 Cosmos DB를 활용해 간단한 영화 정보에 대한 질문에 답변해주는 챗봇입니다. Retrieval-Augmented Generation (RAG) 구조로 작동하며, 질문에 대해 관련 영화 정보를 검색한 후 GPT 모델을 사용해 자연어로 응답을 생성합니다.

## 프로젝트 구조

```
.
├── README.md               # 프로젝트 설명 문서
├── data/                   # 데이터셋 디렉토리
│   ├── MovieLens-4489-256D.json    # 벡터화된 영화 정보 JSON
│   └── MovieLens-4489-256D.zip     # 원본 압축 파일
├── main_sl.py              # Streamlit 기반 UI 실행 파일
├── rag/                    # Python 가상환경 디렉토리 (venv)
├── rag_env.env             # 환경 변수 파일 (API 키, 엔드포인트 등)
├── requirements.txt        # 필요한 Python 패키지 목록
└── src/                    # 주요 Python 모듈 모음
    ├── main.py                   # Gradio 기반 UI 실행 파일 (비사용)
    ├── db_setup.py              # Cosmos DB 설정 및 컨테이너 생성
    ├── insert_data.py           # 데이터 삽입 로직
    ├── embedding.py             # 텍스트 임베딩 생성 함수
    ├── search.py                # 벡터 기반 유사도 검색 및 캐시 조회
    └── completion.py            # GPT 응답 생성 및 캐시 저장
```

## 가상환경 설정

```bash
python -m venv rag
source rag/bin/activate  # 또는 Windows: rag\Scripts\activate
pip install -r requirements.txt
```

## 환경 변수 설정

`rag_env.env` 파일을 생성하고 다음 항목들을 채워주세요:

```
# Cosmos DB 설정
cosmos_uri=...
cosmos_key=...
cosmos_database_name=...
cosmos_collection_name=vectorstore
cosmos_cache_collection_name=vectorcache
cosmos_vector_property_name=vector

# OpenAI - 임베딩
openai_embeddings_endpoint=...
openai_embeddings_key=...
openai_embeddings_deployment=text-embedding-3-small
openai_embeddings_dimensions=1536

# OpenAI - 응답 생성
openai_completions_endpoint=...
openai_completions_key=...
openai_completions_deployment=gpt-35-turbo
openai_api_version=2023-05-15
```

## 사용된 모델

- **임베딩 모델**: `text-embedding-3-small` (1536 dimensions)
- **응답 생성 모델**: `gpt-35-turbo`

## 사용된 데이터셋

**MovieLens-4489-256D.json**

- 약 4,489개의 영화 정보를 `text-embedding-3-small` 모델로 벡터화한 결과가 포함된 JSON 파일입니다.
- 이번 실습에서는 임베딩 과정을 포함하기 때문에 사전에 벡터화된 결과를 사용하지는 않습니다.

## 실행 방법

### Streamlit 실행

```bash
streamlit run main_sl.py -- --skip-insert
```

- `--skip-insert` 옵션을 빼면 실행 시 데이터가 Cosmos DB에 삽입됩니다.

## 기능 요약

- 사용자 질문을 OpenAI 임베딩 모델로 벡터화
- Cosmos DB에서 벡터 유사도 기반으로 관련 영화 검색
- 검색 결과를 바탕으로 GPT가 자연어 답변 생성
- 동일 질문에 대해서는 캐시된 응답을 빠르게 제공

## 📌 주요 모듈 설명

| 파일             | 설명                                           |
| ---------------- | ---------------------------------------------- |
| `main_sl.py`     | Streamlit 기반 UI. 질문 입력 및 응답 출력 담당 |
| `db_setup.py`    | Cosmos DB 컨테이너 생성 및 설정                |
| `insert_data.py` | JSON 데이터를 Cosmos DB에 삽입                 |
| `embedding.py`   | 입력 텍스트를 OpenAI 임베딩 API로 벡터화       |
| `search.py`      | 벡터 검색 및 캐시 조회 로직                    |
| `completion.py`  | GPT를 활용해 응답 생성 및 캐시 저장            |

## 참고 사항

- Cosmos DB는 **벡터 검색 기능이 지원되는 API**를 사용해야 합니다 (예: Azure Cosmos DB for NoSQL).
- 임베딩과 응답 생성을 위한 OpenAI 리전이 다른 경우, 각 클라이언트를 분리하여 설정할 수 있도록 구성되어 있습니다.
- 현재 UI는 Streamlit 기반이며, Gradio 버전은 `src/main.py`에 포함되어 있습니다.

---

이 프로젝트는 Azure 기반 기능을 활용해 간단한 RAG 구조의 영화 챗봇을 만들어보는 실습 예제입니다.

Microsoft에서 제공된 [문서](https://learn.microsoft.com/ko-kr/azure/cosmos-db/gen-ai/rag-chatbot)를 참고했습니다.
