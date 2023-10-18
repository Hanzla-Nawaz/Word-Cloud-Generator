import streamlit as st
from wordcloud import WordCloud, STOPWORDS
from io import BytesIO
import base64
import pandas as pd
import io
from PIL import Image
from PyPDF2 import PdfReader
import re  # Import the 're' module for regular expressions

# Page layout
st.set_page_config(
    page_title="Word Cloud Generator",
    layout="wide"
)

# Title and description
st.title("Word Cloud Generator")
st.write("Upload one or more documents (docx, txt, pdf, or any format) and create a word cloud.")

# Upload file(s)
uploaded_files = st.file_uploader("Upload document(s):", type=["docx", "txt", "pdf"], accept_multiple_files=True)

# Stopwords checkbox
use_stopwords = st.checkbox("Remove Common Stopwords")

# Word cloud size selection
wordcloud_width = st.sidebar.slider("Word Cloud Width", 200, 1600, 800, step=100)
wordcloud_height = st.sidebar.slider("Word Cloud Height", 200, 1200, 400, step=100)

# Initialize wordcloud as None
wordcloud = None

# Initialize text as an empty string
text = ""

# Create word cloud
if uploaded_files:
    for uploaded_file in uploaded_files:
        file_extension = uploaded_file.name.split('.')[-1]
        if file_extension == "pdf":
            pdf_reader = PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        else:
            text += uploaded_file.read().decode('utf-8', errors='ignore')

    if use_stopwords:
        stopwords = set(STOPWORDS)
        # Modify the regular expression pattern for tokenization
        words = re.findall(r'\w+', text)  # This pattern extracts words
        text = ' '.join(words)  # Join the words back into a string
        if len(text) > 0:  # Check if there is at least one word
            wordcloud = WordCloud(stopwords=stopwords, background_color='white', width=wordcloud_width, height=wordcloud_height).generate(text)
        else:
            st.warning("No words found in the document(s) after removing stopwords.")
    else:
        if len(text) > 0:  # Check if there is at least one word
            wordcloud = WordCloud(background_color='white', width=wordcloud_width, height=wordcloud_height).generate(text)
        else:
            st.warning("No words found in the document(s).")

    if wordcloud is not None:
        # Display the word cloud without specifying width
        st.image(wordcloud.to_array())

# ...

# Checkbox for selecting specific words
select_specific_words = st.checkbox("Select Specific Words")

# Initialize selected_words as an empty list
selected_words = []

if select_specific_words:
    # Extract words from the document (modify this logic accordingly)
    words = text.split()
    selected_words = st.multiselect("Select specific words:", list(set(words)))

# Create word cloud for selected words with frequencies and relative scaling
selected_wordcloud = None
selected_word_counts = {}

if len(selected_words) > 0:
    selected_word_counts = {word: words.count(word) for word in selected_words}
    
    # Determine the maximum frequency to calculate relative scaling
    max_frequency = max(selected_word_counts.values())
    
    # Calculate relative scaling for word cloud
    relative_scaling = 0.5  # Adjust this value as needed
    
    # Create word cloud with relative scaling
    selected_wordcloud = WordCloud(
        width=wordcloud_width,
        height=wordcloud_height,
        relative_scaling=relative_scaling
    ).generate_from_frequencies(selected_word_counts)

# Display the word frequencies for selected words in a table
if selected_word_counts:
    selected_word_freq_df = pd.DataFrame(selected_word_counts.items(), columns=["Word", "Frequency"])
    st.subheader("Word Frequencies for Selected Words")
    st.dataframe(selected_word_freq_df)

# Display the word cloud for selected words with frequencies and relative scaling
if selected_wordcloud is not None:
    st.subheader("Word Cloud for Selected Words with Frequency-Based Sizing")
    st.image(
        selected_wordcloud.to_array(),
        width=wordcloud_width,
        caption="Word Cloud for Selected Words (Sized by Frequency)"
    )
   
# Create a table with word frequencies for common stopwords
if use_stopwords:
    common_words = [word for word in text.split() if word in STOPWORDS]
    if common_words:
        common_word_counts = pd.Series(common_words).value_counts().reset_index()
        common_word_counts.columns = ["Word", "Frequency"]
        st.subheader("Word Frequencies for Common Stopwords")
        st.dataframe(common_word_counts.head(50))
    else:
        st.sidebar.warning("No common stopwords found in the document.")



# Create a table with word frequencies
if len(text) > 0:
    words = text.split()
    word_counts = pd.Series(words).value_counts().reset_index()
    word_counts.columns = ["Word", "Frequency"]
    st.subheader("Word Frequencies (Top 50)")
    st.dataframe(word_counts.head(50))

# Checkbox for filtering words by frequency and threshold
filter_words_by_frequency = st.sidebar.checkbox("Filter Words by Frequency")
threshold = st.sidebar.number_input("Threshold", min_value=1, value=5)
frequency_filter = st.sidebar.selectbox("Filter Type", ["None", "Greater Than", "Less Than"])

# Initialize filtered_wordcloud as None
filtered_wordcloud = None

if filter_words_by_frequency:
    # Filter words by frequency based on user-selected threshold
    if frequency_filter == "Greater Than":
        filtered_word_counts = word_counts[word_counts["Frequency"] > threshold]
    elif frequency_filter == "Less Than":
        filtered_word_counts = word_counts[word_counts["Frequency"] < threshold]
    else:
        filtered_word_counts = word_counts  # No frequency filtering

    if not filtered_word_counts.empty:
        # Create a filtered text containing only the selected words
        filtered_text = " ".join([word for word in words if word in filtered_word_counts["Word"].values])

    try:
        # Display the word cloud for filtered words or an error message
        if filtered_text:
            filtered_wordcloud = WordCloud(width=wordcloud_width, height=wordcloud_height).generate(filtered_text)
            st.subheader("Word Cloud for Filtered Words by Frequency")
            st.image(filtered_wordcloud.to_array())
        else:
            st.warning("No words found after filtering. Please adjust your filter criteria.")
    except ValueError as e:
        st.warning("No words found after filtering. Please adjust your filter criteria.")
        

# Display the word cloud for filtered words or an error message
if filtered_wordcloud is not None:
    st.subheader("Word Cloud for Filtered Words by Frequency")
    st.image(filtered_wordcloud.to_array())


        

# Export options
st.sidebar.subheader("Export Word Cloud")
export_format = st.sidebar.selectbox("Select Export Format", ["PNG", "JPEG", "Custom Resolution"])
if export_format == "Custom Resolution":
    custom_width = st.sidebar.number_input("Custom Width:", min_value=100, max_value=4000, value=wordcloud_width)
    custom_height = st.sidebar.number_input("Custom Height:", min_value=100, max_value=4000, value=wordcloud_height)
else:
    custom_width = wordcloud_width
    custom_height = wordcloud_height

if st.sidebar.button("Export Word Cloud"):
    if wordcloud is not None:
        if export_format == "PNG":
            wordcloud.to_file("wordcloud.png")
            st.success("Word Cloud saved as PNG.")
        elif export_format == "JPEG":
            wordcloud.to_file("wordcloud.jpeg")
            st.success("Word Cloud saved as JPEG.")
        elif export_format == "Custom Resolution":
            wordcloud.to_file("wordcloud_custom_resolution.png", width=custom_width, height=custom_height)

            


# Social media accounts
st.sidebar.title("Add Social Media Accounts")
facebook = st.sidebar.text_input("Facebook:")
twitter = st.sidebar.text_input("Twitter:")
linkedin = st.sidebar.text_input("LinkedIn:")
github = st.sidebar.text_input("GitHub:")

# Display social media links
if facebook or twitter or linkedin or github:
    st.sidebar.subheader("Your Social Media Links:")
    if facebook:
        st.sidebar.markdown(f"[Facebook]({facebook})")
    if twitter:
        st.sidebar.markdown(f"[Twitter]({twitter})")
    if linkedin:
        st.sidebar.markdown(f"[LinkedIn]({linkedin})")
    if github:
        st.sidebar.markdown(f"[GitHub]({github})")
