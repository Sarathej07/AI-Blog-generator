import streamlit as st
import re
from typing import List, Optional, TypedDict
from langgraph.graph import StateGraph
from langgraph.graph import END, START, MessageGraph

from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
os.environ["OPENAI_API_KEY"]=os.getenv("OPENAI_API_KEY")

from langgraph.graph import StateGraph, END
from openai import OpenAI

class State(TypedDict):
    keyword: str
    titles: List[str]
    selected_title: Optional[str]
    blog_content: Optional[str]

client = OpenAI()

def generate_titles(state: State):
    """Generates blog titles based on a keyword."""
    prompt = f"""
Task: Generate compelling blog title options about '{state['keyword']}'.

Instructions:
- Provide exactly 5 numbered title options.
- Each title MUST adhere to the following criteria:
    1. **Keyword Inclusion:**  Incorporate the keyword '{state['keyword']}' within the first three words to ensure relevance and SEO.
    2. **Conciseness:** Keep each title under 60 characters for readability and to avoid truncation in search results.
    3. **Power Words:**  Enhance titles with strong power words to increase click-through rates. Examples of power words include: 'Essential', 'Definitive', 'Ultimate', 'Secrets', 'Tips', 'Strategies', 'Boost', 'Unlock', 'Transform', 'Master', 'Guide', 'Powerful', 'Top', 'Best'.
    4. **Intrigue & Value:** Titles should be intriguing and clearly communicate the value proposition of the blog post to attract readers.
    5. **Target Audience Focus:** Consider the target audience and tailor the titles to resonate with their interests and needs related to '{state['keyword']}'.

Example Titles (for keyword 'digital marketing'):
1. Digital Marketing: The Ultimate Guide for Beginners
2. Essential Digital Marketing Strategies You Need Now
3. Boost Your Business with Digital Marketing Secrets
4. Top Digital Marketing Tips to Master in 2025
5. Definitive Guide: Digital Marketing for E-commerce

Format:
Return ONLY a numbered list of titles, with each title on a new line.

Example Output:
1. [Title Option 1]
2. [Title Option 2]
3. [Title Option 3]
4. [Title Option 4]
5. [Title Option 5]
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=200
        )
        raw_output = response.choices[0].message.content.strip()
        titles = [line.split(". ", 1)[1] for line in raw_output.split("\n") if ". " in line][:5] # Increased to 5 titles to match prompt
        return {"titles": titles}
    except Exception as e:
        return {"titles": [], "error": str(e)}

def generate_content(state: State):
    """Generates a detailed blog post based on the selected title."""
    prompt = f"""
Task: Create a comprehensive and engaging 1500-word blog post on the topic: "{state['selected_title']}".

Instructions:
- **Word Count:**  The blog post MUST be approximately 1500 words to provide in-depth coverage.
- **Structure:** Organize the blog post with clear markdown formatting for optimal readability:
    ```markdown
    # {state['selected_title']}  [Use the selected title as the main heading]

    ## Introduction
    [Compelling introduction to hook the reader and outline the blog post's scope]

    ## Main Content
    [In-depth discussion divided into 4-6 key sections, each exploring a significant aspect of the topic. Use '## Section Title' for each section.]

    ### Engaging Subsections
    [Within each main section, use '### Subsection Title' to further break down information and improve readability. Aim for 2-3 subsections per main section as needed.]

    ## Conclusion
    [Summarize the key takeaways and provide a strong concluding statement. Consider a call to action or further questions for the reader.]
    ```
- **Content Depth & Engagement:**
    - **Practical Examples:**  Integrate real-world examples and case studies to illustrate points and enhance understanding. Aim for at least 3-5 practical examples throughout the post.
    - **Statistics & Data:**  Incorporate relevant statistics and data to support claims and add credibility. Include at least 2-3 data points or statistical references where appropriate. (If specific statistics are unavailable, suggest placeholders like '[Insert relevant statistic here with source]').
    - **Actionable Advice:** Provide practical, actionable advice and tips that readers can implement.
    - **Engaging Tone:** Write in an engaging, informative, and slightly authoritative tone. Avoid overly casual or overly technical language unless appropriate for the topic.
    - **SEO Considerations:** Naturally weave in keywords related to "{state['keyword']}" and "{state['selected_title']}" throughout the content for search engine optimization.

- **Formatting:** Ensure proper use of headings, subheadings, bullet points (where applicable), and paragraph breaks for readability in markdown.

Example:
[Assume state['selected_title'] is "Essential Guide: Mastering Keyword Research"]

# Essential Guide: Mastering Keyword Research

## Introduction
[Introduction about the importance of keyword research...]

## Section 1: Understanding Keyword Research Fundamentals
### What are Keywords and Why They Matter
[Explanation of keywords...]
### Types of Keywords: Head, Body, and Long-Tail
[Description of different keyword types...]

## Section 2:  [Further sections and subsections following the structure]

## Conclusion
[Concluding remarks and call to action...]
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=3000
        )
        content = response.choices[0].message.content.strip()
        return {"blog_content": content}
    except Exception as e:
        return {"blog_content": "", "error": str(e)}

def create_workflow():
    workflow = StateGraph(State)
    workflow.add_node("generate_titles", generate_titles)
    workflow.add_node("generate_content", generate_content)
    workflow.set_entry_point("generate_titles")

    def route_after_titles(state: State):
        return "generate_content" if state.get("selected_title") else END

    workflow.add_conditional_edges("generate_titles", route_after_titles)
    workflow.add_edge("generate_content", END)

    return workflow.compile()

st.set_page_config(page_title="AI Blog Generator", page_icon="✍️") 
st.title("✍️ AI Blog Generator")
st.markdown("Generate engaging blog posts in minutes using AI. Simply enter a keyword and let the magic happen!")

if 'blog_state' not in st.session_state:
    st.session_state.blog_state = {
        "keyword": "",
        "titles": [],
        "selected_title": None,
        "blog_content": None
    }

keyword = st.text_input("Enter your blog topic keyword:", value=st.session_state.blog_state["keyword"], placeholder="e.g., 'sustainable living tips'")

col1, col2, col3 = st.columns([2, 1, 2]) 

with col2:
    generate_titles_button = st.button("✨ Generate Titles", use_container_width=True) 

if generate_titles_button and keyword.strip():
    st.session_state.blog_state["keyword"] = keyword.strip() 
    st.session_state.blog_state["titles"] = [] 
    st.session_state.blog_state["selected_title"] = None 
    st.session_state.blog_state["blog_content"] = None 
    with st.spinner("Generating title options..."):
        app = create_workflow() 
        new_state = app.invoke({"keyword": st.session_state.blog_state["keyword"], "titles": [], "selected_title": None, "blog_content": None})
        if new_state.get("titles"):
            st.session_state.blog_state.update({"titles": new_state["titles"]})
        else:
            st.error("Failed to generate titles. Please try again or check your keyword.") 
            
if st.session_state.blog_state["titles"]:
    st.subheader("💡 Generated Titles")
    title_options = st.session_state.blog_state["titles"]
    if title_options:
        selected_title_index = st.selectbox("Choose a title for your blog post:", range(len(title_options)), format_func=lambda x: f"{x+1}. {title_options[x]}") # Selectbox for titles
        st.session_state.blog_state["selected_title"] = title_options[selected_title_index] 

        col1_content, col2_content, col3_content = st.columns([2, 1, 2]) 
        with col2_content:
            generate_content_button = st.button("✍️ Generate Blog Post", use_container_width=True, disabled=not st.session_state.blog_state["selected_title"]) # Button to generate content, disabled if no title selected

        if generate_content_button:
            st.session_state.blog_state["blog_content"] = None 
            with st.spinner("Writing your blog post... This may take a few minutes."): 
                app = create_workflow() 
                final_state = app.invoke(st.session_state.blog_state)
                if final_state.get("blog_content"):
                    st.session_state.blog_state.update(final_state)
                else:
                    st.error("Failed to generate blog content. Please try again.") 
    else:
        st.info("No titles generated yet. Please enter a keyword and click 'Generate Titles'.") 

if st.session_state.blog_state["blog_content"]:
    st.subheader("📝 Blog Post")
    st.markdown(st.session_state.blog_state["blog_content"])
    st.download_button(
        label="⬇️ Download Blog Post as Markdown",
        data=st.session_state.blog_state["blog_content"],
        file_name=f"{st.session_state.blog_state['selected_title']}.md",
        mime="text/markdown"
    )

if st.button("🔄 Reset", use_container_width=True):
    st.session_state.blog_state = {"keyword": "", "titles": [], "selected_title": None, "blog_content": None}
    st.rerun() 