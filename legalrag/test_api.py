"""
Quick test script for LegalRAG API
Run this after starting the server to verify everything works
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test the root endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_upload(pdf_path):
    """Test document upload"""
    print(f"Testing upload with {pdf_path}...")
    with open(pdf_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/upload", files=files)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Document ID: {data['document_id']}")
        print(f"Filename: {data['filename']}")
        print(f"Total chunks: {data['total_chunks']}")
        return data['document_id']
    else:
        print(f"Error: {response.text}")
        return None
    print()


def test_search(query, top_k=3):
    """Test semantic search"""
    print(f"Testing search for: '{query}'...")
    payload = {
        "query": query,
        "top_k": top_k
    }
    response = requests.post(f"{BASE_URL}/search", json=payload)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Query: {data['query']}")
        print(f"Total results: {data['total_results']}")
        print("\nTop results:")
        for i, result in enumerate(data['results'][:3], 1):
            print(f"\n{i}. Score: {result['similarity_score']}")
            print(f"   Page: {result['metadata']['page']}")
            print(f"   Text preview: {result['text'][:200]}...")
    else:
        print(f"Error: {response.text}")
    print()


def test_list_documents():
    """Test listing all documents"""
    print("Testing list documents...")
    response = requests.get(f"{BASE_URL}/documents")

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total documents: {data['total_documents']}")
        for doc in data['documents']:
            print(f"- {doc['filename']} (ID: {doc['document_id']}, Chunks: {doc['total_chunks']})")
    else:
        print(f"Error: {response.text}")
    print()


def test_delete(document_id):
    """Test document deletion"""
    print(f"Testing delete for document {document_id}...")
    response = requests.delete(f"{BASE_URL}/documents/{document_id}")

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Message: {data['message']}")
        print(f"Chunks deleted: {data['chunks_deleted']}")
    else:
        print(f"Error: {response.text}")
    print()


if __name__ == "__main__":
    print("="*50)
    print("LegalRAG API Test Script")
    print("="*50)
    print()

    # Test health check
    test_health_check()

    # Test upload (replace with actual PDF path)
    print("To test upload, uncomment and provide a PDF path:")
    print("# doc_id = test_upload('path/to/your/document.pdf')")
    print()

    # Test search (only works after uploading documents)
    print("To test search (after uploading documents):")
    print("# test_search('your search query here')")
    print()

    # Test listing documents
    test_list_documents()

    print("="*50)
    print("Test complete!")
    print("="*50)
