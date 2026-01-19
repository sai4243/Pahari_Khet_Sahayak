# 🌾 Pahari Khet Sahayak (Mountain Farm Assistant)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Computer%20Vision-orange)
![Gemini Pro](https://img.shields.io/badge/AI-Gemini%20Pro-8E75B2)
![License](https://img.shields.io/badge/License-MIT-green)

> **An AI-powered hybrid agricultural assistant designed to bridge the digital divide for farmers in the Himalayan region of Uttarakhand.**

---

## 📖 Table of Contents
- [About the Project](#-about-the-project)
- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Methodology](#-methodology)
- [Tech Stack](#-tech-stack)
- [Installation & Setup](#-installation--setup)
- [Performance Metrics](#-performance-metrics)
- [Contributors](#-contributors)
- [License](#-license)

---

## 🏔️ About the Project

Farmers in the Indian Himalayas, specifically in Uttarakhand, face unique challenges: difficult terrain, diverse microclimates, and—most critically—**intermittent internet connectivity**. Existing digital tools often fail because they rely heavily on continuous cloud access and provide generic advice that doesn't account for local soil conditions.

**Pahari Khet Sahayak** addresses this digital divide with a **Hybrid Online-Offline Architecture**. It utilizes a Retrieval-Augmented Generation (RAG) framework that queries government APIs when online, while seamlessly reverting to an on-device semantic search over a pre-packaged knowledge base (FAISS) when offline.

This system empowers farmers to:
* Diagnose crop diseases using just a phone camera.
* Receive localized crop recommendations based on soil health cards.
* Access advisory services via voice or text in local dialects (Hindi/English).

---

## 🏗️ System Architecture

The system follows a unified pipeline designed for resilience in low-connectivity zones. As illustrated in our architectural design:
<img width="1171" height="432" alt="image" src="https://github.com/user-attachments/assets/a4a074ea-e507-42e5-b68c-e599af5f210c" />


1.  **Multimodal Input Layer:**
    * **Uttarakhand Farmer:** Interacts with the system via mobile.
    * **Voice/Text Interface:** Supports Hindi and English inputs.
    * **Image Upload:** Accepts crop photos for visual diagnosis.

2.  **Validation & Processing:**
    * [cite_start]**Input Validation:** A "Classify-First" module filters irrelevant queries before they reach heavy computation models[cite: 323].
    * **Chatbot Backend (LLM):** Valid text queries are processed by a Large Language Model fine-tuned on local crop data.
    * **Computer Vision Model:** Images are routed to a YOLO/ResNet model specifically trained for disease detection.

3.  **Core Intelligence (The RAG Module):**
    * The **RAG Module** acts as the central brain. It dynamically selects the information source based on connectivity.
    * **Online Sources:** Fetches real-time data from **Govt APIs** (e-Kisan, PM-KISAN) and **GIS/Weather Data**.
    * **Offline Sources:** Queries an internal **Offline Cache** using semantic search.

4.  **Output Layer:**
    * **Response Generator:** Synthesizes the retrieved data into personalized advice.
    * **Output Interface:** Delivers the final answer via Audio or Text.

---

## 🚀 Key Features

### 1. 📶 Connectivity-Aware RAG Chatbot
* [cite_start]**Hybrid Logic:** Automatically detects network status to switch between online APIs and offline vectors[cite: 565].
* [cite_start]**Zero-Network Support:** Uses an on-device semantic search (FAISS + Quantized MiniLM) to answer queries when the internet cuts out[cite: 512].

### 2. 🦠 Hierarchical Disease Detection
* [cite_start]**Stage 1 (Triage):** A lightweight **YOLOv8** model identifies the crop type (e.g., Wheat vs. Millet) to filter out non-crop images[cite: 505].
* [cite_start]**Stage 2 (Diagnosis):** The image is routed to a specialized "Expert Model" (e.g., `wheat_disease.pt`) to detect specific diseases like Rust or Blast with high precision.

### 3. 🌱 Precision Crop Recommendation
* [cite_start]**Ensemble Engine:** Uses a **Weighted Majority Voting** system combining Random Forest, SVM, and XGBoost to recommend the best crop based on N, P, K, pH, and rainfall data[cite: 432].
* [cite_start]**Regional Specificity:** Optimized for the specific soil compositions found in the Himalayan region[cite: 338].

---

## 🔬 Methodology

### Data Collection
* [cite_start]**Intent Classification:** A custom dataset of 3,000 agricultural queries, including code-mixed (Hinglish) examples, generated via few-shot prompting[cite: 393].
* [cite_start]**Crop Data:** Standardized datasets with over 10,000 records of soil nutrients (N, P, K) and environmental factors[cite: 394].

### Offline Knowledge Retrieval
We utilize **Facebook AI Similarity Search (FAISS)** to index agricultural documents as dense vectors.
* **Vectorization:** Text chunks are converted into 384-dimensional vectors using `all-MiniLM-L6-v2`.
* [cite_start]**Retrieval:** The system performs an efficient Euclidean distance search to find relevant cures locally, removing the need for cloud dependence[cite: 450].

---

## 💻 Tech Stack

| Component | Technologies Used |
| :--- | :--- |
| **Frontend** | Streamlit, HTML/CSS (Custom Styling) |
| **LLM & AI** | Google Gemini Pro, LangChain, Sentence-Transformers |
| **Vector DB** | FAISS (Facebook AI Similarity Search) |
| **Computer Vision** | Ultralytics YOLOv8, ResNet50, OpenCV |
| **Machine Learning** | Scikit-learn (Random Forest, SVM, XGBoost), Pandas, NumPy |
| **NLP** | BERT (Fine-tuned `bert-base-multilingual-cased`) |
| **External APIs** | OpenWeatherMap, Agmarknet (Govt. of India), Google Custom Search |

---
## 🤝 Contributors

This project was developed by the research team at **Vellore Institute of Technology (VIT)**:

- **Adapa Sai Venkata Teja** – Data Science, Machine Learning & System Integration  
- **Alle Hithesh** – Computer Vision & Model Training  
- **Bandari Rohith** – Backend Logic & API Integration  

**Supervisor:**  
- **Dr. Parthasarathy G.**, School of Computer Science and Engineering, VIT

## ⚙️ Installation & Setup

Follow these steps to run the project locally:

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/pahari-khet-sahayak.git](https://github.com/your-username/pahari-khet-sahayak.git)
cd pahari-khet-sahayak


