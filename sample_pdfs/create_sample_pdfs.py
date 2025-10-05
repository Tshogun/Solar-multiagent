"""
Create Sample PDF Documents for Testing
This script creates placeholder PDFs with sample NebulaByte content
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from pathlib import Path
from datetime import datetime


def create_pdf(filename, title, content_sections):
    """
    Create a PDF document with given title and content
    
    Args:
        filename: Output filename
        title: Document title
        content_sections: List of (section_title, section_content) tuples
    """
    output_path = Path(__file__).parent / filename
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    
    # Container for elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='darkblue',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = styles['Heading2']
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )
    
    # Add title
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Add metadata
    date_str = datetime.now().strftime("%B %Y")
    elements.append(Paragraph(f"<i>NebulaByte Knowledge Base - {date_str}</i>", styles['Normal']))
    elements.append(Spacer(1, 0.5 * inch))
    
    # Add content sections
    for section_title, section_content in content_sections:
        elements.append(Paragraph(section_title, heading_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        for paragraph in section_content:
            elements.append(Paragraph(paragraph, body_style))
            elements.append(Spacer(1, 0.1 * inch))
        
        elements.append(Spacer(1, 0.3 * inch))
    
    # Build PDF
    doc.build(elements)
    print(f"✓ Created: {filename}")


def main():
    """Create all sample PDFs"""
    
    # PDF 1: Introduction to AI and ML
    create_pdf(
        "1_intro_to_ai_ml.pdf",
        "Introduction to Artificial Intelligence and Machine Learning",
        [
            ("What is Artificial Intelligence?", [
                "Artificial Intelligence (AI) is the simulation of human intelligence processes by machines, especially computer systems. These processes include learning, reasoning, and self-correction.",
                "AI can be categorized into narrow AI (designed for specific tasks) and general AI (capable of performing any intellectual task that a human can do). Current AI systems are predominantly narrow AI.",
                "Applications of AI include natural language processing, computer vision, robotics, and expert systems. These technologies are transforming industries from healthcare to finance."
            ]),
            ("Machine Learning Fundamentals", [
                "Machine Learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves.",
                "The three main types of machine learning are: supervised learning (learning from labeled data), unsupervised learning (finding patterns in unlabeled data), and reinforcement learning (learning through trial and error).",
                "Common machine learning algorithms include decision trees, neural networks, support vector machines, and ensemble methods. Each has its strengths and is suited for different types of problems."
            ]),
            ("Deep Learning and Neural Networks", [
                "Deep Learning is a specialized form of machine learning based on artificial neural networks. It uses multiple layers of processing to extract progressively higher-level features from raw input.",
                "Convolutional Neural Networks (CNNs) are particularly effective for image processing tasks, while Recurrent Neural Networks (RNNs) excel at sequence data like text and time series.",
                "Recent advances in deep learning have led to breakthroughs in image recognition, natural language processing, and game playing, achieving human-level or superhuman performance in many domains."
            ])
        ]
    )
    
    # PDF 2: Large Language Models
    create_pdf(
        "2_large_language_models.pdf",
        "Large Language Models: Architecture and Applications",
        [
            ("The Transformer Architecture", [
                "The Transformer architecture, introduced in 2017, revolutionized natural language processing. It relies entirely on attention mechanisms to draw global dependencies between input and output.",
                "Key components include self-attention layers, position encodings, and feed-forward networks. The multi-head attention mechanism allows the model to focus on different aspects of the input simultaneously.",
                "Transformers can be parallelized more effectively than recurrent models, making them much faster to train on modern hardware. This scalability enabled the development of very large language models."
            ]),
            ("GPT and BERT Models", [
                "GPT (Generative Pre-trained Transformer) uses a decoder-only architecture and is trained to predict the next token in a sequence. It excels at text generation tasks.",
                "BERT (Bidirectional Encoder Representations from Transformers) uses an encoder-only architecture and is trained on masked language modeling. It's particularly effective for understanding tasks.",
                "Both models use transfer learning: they're pre-trained on large text corpora and then fine-tuned for specific tasks. This approach has become standard in NLP."
            ]),
            ("Modern LLMs and Applications", [
                "Modern large language models like GPT-4, Claude, and LLaMA contain billions of parameters and are trained on diverse internet text. They can perform a wide variety of language tasks without task-specific training.",
                "Applications include content generation, code completion, question answering, translation, summarization, and conversational AI. These models are being integrated into numerous products and services.",
                "Challenges include computational costs, potential biases in training data, hallucination of false information, and questions around copyright and data usage."
            ])
        ]
    )
    
    # PDF 3: Computer Vision
    create_pdf(
        "3_computer_vision.pdf",
        "Computer Vision: From Basics to Advanced Applications",
        [
            ("Image Processing Fundamentals", [
                "Computer vision enables machines to interpret and understand visual information from the world. It combines image processing, pattern recognition, and machine learning techniques.",
                "Basic image processing operations include filtering, edge detection, color space transformations, and morphological operations. These form the foundation for more complex vision tasks.",
                "Feature extraction techniques like SIFT, SURF, and HOG identify distinctive patterns in images that can be used for object recognition and matching."
            ]),
            ("Convolutional Neural Networks for Vision", [
                "CNNs are the dominant architecture for computer vision tasks. They use convolutional layers to automatically learn hierarchical feature representations from images.",
                "Early layers detect simple features like edges and textures, while deeper layers recognize complex patterns and objects. Pooling layers reduce spatial dimensions while preserving important information.",
                "Popular CNN architectures include ResNet, VGG, Inception, and EfficientNet. Each introduces innovations in depth, width, or computational efficiency."
            ]),
            ("Vision Applications", [
                "Object detection systems like YOLO and Faster R-CNN can identify and locate multiple objects in images in real-time. These are used in autonomous vehicles and surveillance.",
                "Semantic segmentation assigns a class label to each pixel in an image, enabling precise understanding of scene composition. Instance segmentation further distinguishes individual objects.",
                "Other applications include facial recognition, medical image analysis, optical character recognition, and augmented reality. Computer vision is transforming industries from healthcare to retail."
            ])
        ]
    )
    
    # PDF 4: NLP and Text Processing
    create_pdf(
        "4_nlp_text_processing.pdf",
        "Natural Language Processing: Techniques and Applications",
        [
            ("Text Preprocessing", [
                "Text preprocessing is crucial for NLP tasks. Common steps include tokenization (splitting text into words or subwords), lowercasing, and removing punctuation and stop words.",
                "Stemming and lemmatization reduce words to their root forms. Stemming uses simple rules while lemmatization uses vocabulary and morphological analysis.",
                "Modern approaches often use subword tokenization like Byte-Pair Encoding (BPE) or WordPiece, which balance vocabulary size with the ability to handle rare words."
            ]),
            ("Word Embeddings and Representations", [
                "Word embeddings represent words as dense vectors in a continuous space, capturing semantic relationships. Words with similar meanings have similar vector representations.",
                "Word2Vec and GloVe were early popular methods. They create static embeddings where each word has a single representation regardless of context.",
                "Contextual embeddings from models like BERT and GPT provide different representations for the same word based on its context, capturing nuances in meaning."
            ]),
            ("NLP Tasks and Applications", [
                "Named Entity Recognition (NER) identifies and classifies named entities like persons, organizations, and locations in text. It's essential for information extraction.",
                "Sentiment analysis determines the emotional tone of text, used extensively for social media monitoring and customer feedback analysis.",
                "Machine translation, question answering, text summarization, and dialogue systems are other key NLP applications powered by modern language models."
            ])
        ]
    )
    
    # PDF 5: AI Ethics and Future
    create_pdf(
        "5_ai_ethics_future.pdf",
        "AI Ethics, Challenges, and Future Directions",
        [
            ("Ethical Considerations in AI", [
                "AI systems can perpetuate and amplify biases present in training data, leading to unfair outcomes in hiring, lending, criminal justice, and other domains.",
                "Privacy concerns arise from AI's ability to analyze vast amounts of personal data. Ensuring data protection and user consent is crucial.",
                "Transparency and explainability are important for building trust in AI systems, especially in high-stakes applications like healthcare and autonomous vehicles."
            ]),
            ("AI Safety and Alignment", [
                "AI safety research focuses on ensuring AI systems behave as intended and don't cause unintended harm. This becomes more critical as systems become more powerful.",
                "The alignment problem asks how to ensure AI systems' goals align with human values and intentions. This is particularly important for advanced AI systems.",
                "Robustness and reliability are essential. AI systems should handle edge cases gracefully and fail safely when encountering unexpected inputs."
            ]),
            ("Future of AI", [
                "Artificial General Intelligence (AGI) - systems with human-level intelligence across all domains - remains a long-term goal. Current AI is still narrow and specialized.",
                "Multimodal AI systems that can process and reason across text, images, audio, and other modalities are an active research area showing promising results.",
                "The future likely involves more human-AI collaboration, with AI augmenting human capabilities rather than replacing humans entirely. Ongoing research focuses on making AI more efficient, interpretable, and aligned with human values."
            ])
        ]
    )
    
    print("\n✓ All sample PDFs created successfully!")
    print(f"Location: {Path(__file__).parent}")


if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("Error: reportlab not installed.")
        print("Install with: pip install reportlab")