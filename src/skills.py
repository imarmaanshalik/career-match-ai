SKILLS = [
    "python",
    "java",
    "c++",
    "c",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "fastapi",
    "flask",
    "django",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "machine learning",
    "deep learning",
    "nlp",
    "computer vision",
    "artificial intelligence",
    "data science",
    "data analysis",
    "power bi",
    "tableau",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "git",
    "github",
    "linux",
    "rest api",
    "api",
    "streamlit",
    "langchain",
    "llm",
    "generative ai",
    "rag",
    "opencv",
    "spark",
    "hadoop",
]


def extract_skills(text):
    text = text.lower()

    found = []

    for skill in SKILLS:
        if skill.lower() in text:
            found.append(skill)

    return sorted(set(found))
