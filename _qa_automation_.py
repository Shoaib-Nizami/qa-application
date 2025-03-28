import streamlit as st 
from qat_load_test import loadTest


# Custom CSS for info icon and tooltip
st.markdown("""
<style>
/* Info icon style */
.info-icon {
    font-size: 16px;
    color: #1E90FF;
    cursor: pointer;
    margin-left: 5px;
}

/* Tooltip style */
.tooltip {
    position: relative;
    display: inline-block;
}

.tooltip .tooltiptext {
    visibility: hidden;
    width: 300px;
    background-color: #f9f9f9;
    color: #000;
    text-align: left;
    border-radius: 5px;
    padding: 10px;
    position: absolute;
    z-index: 1;
    bottom: 125%; /* Position above the icon */
    left: 50%;
    margin-left: -150px; /* Center the tooltip */
    opacity: 0;
    transition: opacity 0.3s;
    border: 1px solid #ddd;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.tooltip:hover .tooltiptext {
    visibility: visible;
    opacity: 1;
}
</style>
""", unsafe_allow_html=True)

def qa_automation_page():
    """
    Main Page for QA Automation - Aligned with STLC Cycle
    """
    st.header("QA Automation")

    # Define STLC phases in sequence
    stlc_phase = st.selectbox(
        "Select Phase:",
        [
            "Requirement Analysis",
            "Test Planning",
            "Test Case Development",
            "Test Environment Setup",
            "Test Execution",
            "Test Closure"
        ]
    )

    # Handle the selected STLC phase
    if stlc_phase == "Requirement Analysis":
        st.write("### Requirement Analysis")
        st.markdown("""
        <div class="tooltip">
            <span class="info-icon">??</span>
            <span class="tooltiptext">
                <b>Purpose:</b> Understand and analyze the testing requirements.<br>
                <b>Activities:</b><br>
                - Review software requirements specifications (SRS).<br>
                - Identify testable requirements.<br>
                - Define the scope of testing.
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.info("Requirement analysis features will be added soon.")

    elif stlc_phase == "Test Planning":
        st.write("### Test Planning")
        st.markdown("""
        <div class="tooltip">
            <span class="info-icon">??</span>
            <span class="tooltiptext">
                <b>Purpose:</b> Define the test strategy, scope, resources, and schedule.<br>
                <b>Activities:</b><br>
                - Prepare a test plan document.<br>
                - Allocate resources (team, tools, environment).<br>
                - Define the test schedule and milestones.
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.info("Test planning features will be added soon.")

    elif stlc_phase == "Test Case Development":
        st.write("### Test Case Development")
        st.markdown("""
        <div class="tooltip">
            <span class="info-icon">??</span>
            <span class="tooltiptext">
                <b>Purpose:</b> Create detailed test cases and test scripts.<br>
                <b>Activities:</b><br>
                - Write test cases based on requirements.<br>
                - Review and approve test cases.<br>
                - Prepare test data and scripts.
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.info("Test case development features will be added soon.")

    elif stlc_phase == "Test Environment Setup":
        st.write("### Test Environment Setup")
        st.markdown("""
        <div class="tooltip">
            <span class="info-icon">??</span>
            <span class="tooltiptext">
                <b>Purpose:</b> Set up the hardware, software, and network for testing.<br>
                <b>Activities:</b><br>
                - Configure test servers and databases.<br>
                - Install necessary software and tools.<br>
                - Verify the test environment is ready.
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.info("Test environment setup features will be added soon.")

    elif stlc_phase == "Test Execution":
        st.write("### Test Execution")
        st.markdown("""
        <div class="tooltip">
            <span class="info-icon">??</span>
            <span class="tooltiptext">
                <b>Purpose:</b> Execute test cases and report defects.<br>
                <b>Activities:</b><br>
                - Run test cases and record results.<br>
                - Log defects in a tracking tool.<br>
                - Retest fixed defects.
            </span>
        </div>
        """, unsafe_allow_html=True)
        loadTest.load_test_page()

    elif stlc_phase == "Test Closure":
        st.write("### Test Closure")
        st.markdown("""
        <div class="tooltip">
            <span class="info-icon">??</span>
            <span class="tooltiptext">
                <b>Purpose:</b> Analyze test results, prepare reports, and archive test artifacts.<br>
                <b>Activities:</b><br>
                - Prepare a test summary report.<br>
                - Document lessons learned.<br>
                - Archive test cases, scripts, and results.
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.info("Test closure features will be added soon.")



