import streamlit as st

# Basic page config
st.set_page_config(
    page_title="Article Analysis System",
    page_icon="🔍",
    layout="wide"
)

def main():
    """Minimal test version"""
    st.title("🔍 Article Analysis System")
    st.write("Testing basic functionality...")
    
    # Simple input
    text_input = st.text_area("Enter text:", placeholder="Type something here...")
    
    if st.button("Test Button"):
        if text_input:
            st.success(f"Input received: {len(text_input)} characters")
        else:
            st.warning("No text entered")
    
    # Simple metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Test Metric 1", "100")
    with col2:
        st.metric("Test Metric 2", "200")  
    with col3:
        st.metric("Test Metric 3", "300")

if __name__ == "__main__":
    main()