# Design decisions

The main technical choices in AyurIP-Sahayak: what I chose, why, what it cost, and what I would change. The [README](README.md) explains how everything works; this file explains why it works that way.

Numbers come from `backend/eval/` (38 labelled questions) or from timing the live demo on 1 November 2026.

---

## 1. Retrieve first, then generate

**Decision.** Every question is answered from passages retrieved from my own knowledge base. The model gets the top 6 passages, numbered, and is told to answer only from them and cite each claim as `[n]`.

**Why.** A plain LLM call can't show where an answer came from, and in a legal or medical-adjacent domain an unsourced answer is not useful. With retrieval, every claim links to a page and section the user can check, and when nothing relevant is found the app says so instead of guessing.

**Trade-off.** The app can't answer anything outside its two documents, and a bad retrieval means an incomplete answer.

---

## 2. Gemini embeddings API instead of a local model

**Decision.** Embeddings come from `gemini-embedding-001` (768 dimensions). The first version used `sentence-transformers` (`all-MiniLM-L6-v2`) running locally.

**Why.** The local model brought in PyTorch and Transformers. On Render's free tier the app went over the 512 MiB memory limit, and on my Windows laptop Smart App Control blocked PyTorch's DLLs, so it couldn't start locally either. Moving embeddings to an API cut the runtime dependencies to five packages (FastAPI, uvicorn, `google-genai`, NumPy, `python-dotenv`) and the whole app now runs on Vercel's free tier. Gemini's embeddings are also multilingual, which is what makes Hindi and Kannada questions find English passages.

**Trade-off.** Every question now needs a network call to embed it: retrieval takes 200–350 ms on the live demo, and almost all of that is the embedding call. The stored index is tied to this model, so changing models means re-embedding everything.

---

## 3. No vector database

**Decision.** The index is a `229 × 768` `float32` matrix (0.7 MB, `embeddings.npy`) plus `index.json` for the text and metadata. Search is one NumPy matrix product and a sort.

**Why.** At this size brute-force search is exact and takes about 0.03 ms per query on my laptop (1,000 searches in 28 ms). A vector database would add a service to run, an account and a network hop without making anything faster or more accurate.

**Trade-off.** The whole matrix is loaded into memory on every cold start, and brute force grows linearly with the number of chunks.

**What I'd change.** With tens of thousands of chunks, or if I needed metadata filtering (by document, year or section), I would move to pgvector or Qdrant with an approximate index.

---

## 4. Dense retrieval as the default, not hybrid

**Decision.** `RETRIEVAL_MODE` defaults to `dense`. BM25 and hybrid (BM25 + dense, Reciprocal Rank Fusion with k = 60) are implemented from scratch and kept as baselines.

**Why.** Hybrid search is the usual advice, especially for exact terms like patent numbers, so I expected it to win. I built a labelled evaluation set to check, and it didn't:

| Retriever | Hit@1 | MRR | MRR on identifier queries (5) | MRR on Hindi/Hinglish (4) | MRR on Kannada (5) |
|---|---|---|---|---|---|
| Dense | 0.95 | 0.97 | 1.00 | 1.00 | 0.90 |
| Hybrid | 0.87 | 0.93 | 0.80 | 1.00 | 0.90 |
| BM25 | 0.47 | 0.60 | 0.67 | 0.25 | 0.20 |

Gemini embeddings already ranked statute sections and patent numbers first; fusing in BM25 pushed some correct passages from rank 1 to rank 2 or 3. BM25 can't match Hindi or Kannada questions against English text at all.

**Trade-off.** The evaluation is small (38 questions) and most of the corpus is a document I wrote, so the result may not hold on other documents. That's why the mode is one environment variable away and the evaluation is one command to re-run.

---

## 5. Section-aware chunks that never cross a page

**Decision.** Chunks are packed from whole sentences up to 1,000 characters with about 150 characters of overlap, and they never cross a page or section boundary. Each chunk carries its file, page and section heading. Repeated headers and footers are removed before chunking, and bibliographies are skipped.

**Why.** Citations are the point of the app, so every chunk has to belong to exactly one page and one section. Cutting at sentence boundaries keeps each passage readable when a user opens a citation. Because chunks stop at section ends, most are shorter than the limit: the median is 549 characters (range 70–998).

**Trade-off.** I picked 1,000 / 150 as a sensible starting point and did not compare other sizes. Short chunks at the end of sections carry little context. The journal PDF is in two columns, so some of its section labels are approximate (page numbers are exact).

---

## 6. Streaming over plain HTTP, with sources sent first

**Decision.** `/api/ask/stream` returns newline-delimited JSON: one `sources` event, then many `delta` events, then `done`. The answer model is `gemini-3.5-flash-lite` with minimal thinking.

**Why.** With `gemini-3.6-flash` an answer took 10–13 seconds before anything appeared, which feels broken in a chat UI. Streaming plus the lighter model fixed it. On the live demo (5 questions), sources appear after 0.6–1.0 s, the first words after 1.4–1.8 s, and the full answer is done in 1.6–3.0 s. NDJSON works with a plain `fetch` and a stream reader, so there's no WebSocket server to run on a serverless host.

**Trade-off.** Flash-lite is a smaller model. On my test questions the answers were as good, but I haven't measured answer quality with an evaluation yet.

---

## 7. RAG written by hand, no LangChain or LlamaIndex

**Decision.** PDF cleaning, chunking, BM25, RRF, prompt building and citation parsing are my own code.

**Why.** I wanted to understand and be able to explain every step, and the pipeline is small enough that a framework would have added more code and dependencies than it saved. It also kept the deployment small (decision 2).

**Trade-off.** No ready-made loaders, rerankers or tracing; anything like that I add myself.

---

## 8. One Vercel deployment for frontend and API

**Decision.** Vercel builds the React app, and FastAPI serves both the API and the built frontend from the same domain.

**Why.** One project to deploy, one URL, and no CORS setup. The free Hobby plan is enough.

**Trade-off.** The rate limit (10 questions per visitor per minute) is kept in memory, so each serverless instance counts separately. A shared store such as Upstash Redis would make it global.

---

## 9. An answer judge from a different model family

**Decision.** Answers are written by Gemini and judged by `openai/gpt-oss-120b` on Groq. The judge splits each answer into claims and checks each one against the retrieved passages only, not its own knowledge.

**Why.** A model judging its own family's output tends to approve its own style. Groq's free tier also allows far more requests than the larger Gemini models, whose free quota (20 requests) was too small for 38 answers. To check the judge itself, I planted a false, cited sentence in 15 answers; it flagged all 15.

**Trade-off.** One more API key and provider. The free tier allows about one judge call every 20 seconds, so a full run takes around 15 minutes; answers and judgements are cached so a stopped run resumes. A judge can still miss subtle errors, so I read every judgement by hand.

---

## What I'd do next

1. **A harder evaluation.** Grow the question set to about 60, with more Hindi and Hinglish and more multi-part questions, so Hit@3 (1.00 for dense and hybrid today) can show differences.
2. **pgvector** as an optional index, with a NumPy vs pgvector timing comparison, for when the corpus grows.
3. **Tracing** (for example Langfuse) to see retrieval and generation time per request on the live app.
