import fitz  # PyMuPDF to extract text from PDFs
import re
import json


def extract_text_from_pdf(pdf_path, start_page=6):
    """Extract text from a PDF file starting from a specific page."""
    text = ""
    with fitz.open(pdf_path) as pdf:
        for page_num in range(start_page - 1, len(pdf)):  # Start from the specified page (page 6)
            text += pdf[page_num].get_text()
    return text


def extract_answers_and_explanations(text):
    """
    Extract answers and explanations from the answers text.
    Correct answer is in column 2, and explanation is in column 3.
    """
    # Answer pattern: captures the question number, correct answers, and the explanation text
    answer_pattern = re.compile(r"(\n)(\d+|A\d+)\s+([a-e, ]+)(.*?)(?=\nFL)", re.DOTALL)

    # Explanation pattern: captures the question number and the full explanation before "FL"
    explanation_pattern = re.compile(r"(\n)(\d+|A\d+)\s+([a-e, ]+)(.*?)(?=\nFL)", re.DOTALL)

    answers = {}

    # First, extract the answers and explanations using answer_pattern
    for match in answer_pattern.finditer(text):
        answer_id = match.group(2).strip()  # Question number (e.g., 1, 2, A1, etc.)
        correct_answer = match.group(3) # Correct answer(s) (a, b, c, d, e, or combinations like a,e)
        explanation = match.group(4).strip()  # Explanation for each option (a, b, c, d, e)

        answers[answer_id] = {
            "correct": correct_answer
        }

    # Next, extract the explanation text for each question
    for match in explanation_pattern.finditer(text):
        answer_id = match.group(2).strip()  # Question number (e.g., 1, A1, etc.)
        explanation_text = match.group(4).strip()  # Full explanation (after the correct answers)

        if answer_id in answers:
            answers[answer_id]["explanation"] = {"full": explanation_text}

    # Debugging: Check extracted answers and explanations
    print(f"Debug - Extracted answers and explanations: {answers.keys()}")
    return answers


def extract_questions_and_options(text):
    """
    Extract questions and options from the questions text.
    After 4 options (a, b, c, d), check the next line:
    - If it starts with e), add it as the 5th option.
    - If it does not start with e), discard the additional options.
    - If it starts a new 'Domanda', it marks the next question.
    """
    question_pattern = r"(Domanda\s(?:A?\d+))\s*(.*?)(?=\n[a-e]\))"  # Match question titles and text up until options
    option_pattern = r"(\n)([a-e])\)\s*(.*?)(?=\n(?!Domanda))"  # Capture options a) to e)

    questions = []

    # Find all questions (including "Domanda" and the question body before options)
    question_matches = re.finditer(question_pattern, text, re.DOTALL)

    for match in question_matches:
        title = match.group(1).strip()  # Title of the question (e.g., "Domanda 1")
        question_text = match.group(2).strip()  # Question text (before the first option)

        # Add the title (Domanda X) to the question text
        full_question = f"{title} {question_text}"

        # Extract options for this question
        options = []
        options_text = text[match.end():]  # Capture the part of text after the question

        # Find all options for this specific question (a-e)
        option_matches = re.findall(option_pattern, options_text)

        # Debugging: Display the option matches for this question
        print(f"Debug - Extracted option matches for {title}: {option_matches}")

        # Process options step-by-step
        for i, option in enumerate(option_matches[:5]):  # Limit to the first 5 matches
            option_letter = option[1].strip()  # Option letter (a, b, c, d, e)
            option_text = option[2].strip()  # Option text

            # Concatenate the option letter with its text (e.g., "a) Configurare gli ambienti di test")
            full_option = f"{option_letter}) {option_text}"

            print(f"Debug - Checking option: {full_option}")

            # Add the full option to the options list
            options.append(full_option)

            # If we reach the 5th option, ensure it corresponds to "e)"
            if len(options) == 5:
                if option_letter != "e":  # Check the option letter, not the text
                    print(f"Debug - Discarding 5th option for {title} because it doesn't start with 'e)'.")
                    options = options[:4]  # Remove the 5th option
                break  # Stop after processing the first 5 options

        # Debugging: Final options for the current question
        print(f"Debug - Final Options for {title}: {options}")

        questions.append({"title": title, "question": full_question, "options": options})

    return questions


def generate_quiz_json(questions, answers, output_path):
    """
    Generate a JSON file combining questions, options, answers, and explanations.
    """
    quiz_data = {
        "id": "1",
        "title": "ISTQB Sample Exam",
        "time": "60 minutes",
        "questionList": []
    }

    for question in questions:
        # Normalize question ID
        question_id_match = re.search(r"Domanda\s([A-Z]?\d+)", question["title"])
        if question_id_match:
            question_id = question_id_match.group(1).strip()
        else:
            print(f"Warning: Unable to extract ID for question: {question['title']}")
            continue

        # Prepare question data
        question_data = {
            "question": question["question"],
            "options": question["options"],
        }

        # Match answers
        if question_id in answers:
            question_data["correct"] = answers[question_id]["correct"]
            question_data["explanation"] = answers[question_id]["explanation"]
            print(f"Debug - Found match for question {question_id}: Correct Answer: {answers[question_id]['correct']}, Explanation: {answers[question_id]['explanation']}")
        else:
            print(f"Warning: No answers found for Domanda {question_id}, adding empty fields.")
            question_data["correct"] = []
            question_data["explanation"] = {}

        quiz_data["questionList"].append(question_data)

    with open(output_path, "w") as f:
        json.dump([quiz_data], f, indent=4, ensure_ascii=False)
    print(f"Quiz JSON saved at: {output_path}")


# Paths to your PDFs
questions_pdf_path = "D:/isqtb/ITASTQB-QTEST-FL-2023-A.pdf"
answers_pdf_path = "D:/isqtb/ITASTQB-QTEST-FL-2023-A-SOL.pdf"
output_json_path = "D:/isqtb/JSONS/ITASTQB-QTEST-FL-2023-A.json"

# Extract text from the PDFs, starting from page 8 (index starts before page 8)
questions_text = extract_text_from_pdf(questions_pdf_path, start_page=8)
answers_text = extract_text_from_pdf(answers_pdf_path, start_page=6)  # Answers start from page 6

# Parse the extracted text
parsed_questions = extract_questions_and_options(questions_text)
parsed_answers = extract_answers_and_explanations(answers_text)

# Generate the final JSON
generate_quiz_json(parsed_questions, parsed_answers, output_json_path)
