// script.js
// script.js
document.addEventListener('DOMContentLoaded', () => {
    // Previous background and setup code remains the same

    // Add Experience Data
    const experience = [
            {
            title: "AI Engineer",
            company: "Fime",
            dates: "2025 - Present",
            description: `
            <ul class="experience-list">
                <li>Working in AI team to build and deliver company AI products and AI Agent applications.Working in AI team to build and deliver company AI products and AI Agent applications.</li>
            </ul>
            `,
        },
        {
            title: "AI Engineer",
            company: "Cosywee",
            dates: "2024 - 2025",
            description: `
            <ul class="experience-list">
                <li>Currently curating and expanding datasets to improve Optical Character Recognition (OCR) performance.</li>
                <li>Actively managing and maintaining an OCR model in pre-production, implementing enhancements as needed.</li>
                <li>Developing a Chatbot using Agentic RAG to provide dynamic product pricing based on size and additional items, along with general company information.</li>
            </ul>
            `,
        },
        {
            title: "AI Engineer Intern",
            company: "Cosywee",
            dates: "2024 - 2024",
            description: `
            <ul class="experience-list">
                <li>Constructed a comprehensive company dataset and ground truth labels to support OCR model fine-tuning.</li>
                <li>Fine-Tuned a Pre-trained Model:
                    <ul class="sublist">
                        <li>Optimized a pre-trained TrOCR (Transformer-based OCR model) for general text, numeric, and special character recognition tasks.</li>
                        <li>Adapted the model specifically to the company's proprietary dataset for enhanced accuracy.</li>
                    </ul>
                </li>
                <li>Pre-trained and Fine-Tuned a Custom OCR Model:
                    <ul class="sublist">
                        <li>Developed a CNN-based ResNet-BiLSTM architecture for numeric recognition tasks.</li>
                        <li>Pre-trained the model using a synthetic and open-source dataset containing ~19 million samples.</li>
                        <li>Fine-tuned the model on a proprietary dataset of ~20,000 samples to improve performance and robustness.</li>
                    </ul>
                </li>
                <li>Developed an automation pipeline to connect to a mail server using Microsoft Graph API and locally download mailboxes containing quotations or purchase orders for OCR.</li>
            </ul>


            `,
            // description: "Pre-trained and Fine-tuned a Custom OCR Model"
        },
        {
            title: "Research and Development Mission",
            company: "IMT Mines Ales",
            dates: "2024 - 2024",
            description: `
            <ul class="experience-list">
                <li>Build and compare a regression model to forecast the level of glucose in 30 minutes using a hybrid CNN-LSTM model.</li>
                <li>Build a classification model to classify a patient's state (hyperglycemia, hypoglycemia, normal) based on the recorded data using the same model.</li>
            </ul>
            `,
            // description: "Pre-trained and Fine-tuned a Custom OCR Model"
        },
        {
            title: "Intern",
            company: "GEOCHANVRE",
            dates: "2024 - 2024",
            description: `
            <ul class="experience-list">
                <li>Develop an inventory management application and database for the factory's stock control.</li>
                <li>Integrate QR codes for each product type into the application.</li>
            </ul>
            `,
            // description: "Pre-trained and Fine-tuned a Custom OCR Model"
        },
        {
            title: "Research Assistant",
            company: "ViLa Laboratory",
            dates: "2022 - 2023",
            description: `
            <ul class="experience-list">
                <li>Experiment by training the model with different hyperparameters and collecting a dataset to train the model.</li>
                <li>Assist researchers in various tasks</li>
                <li>Participate in the presentation of a poster on the research theme during the national scientific day.</li>
            </ul>
            `,
            // description: "Pre-trained and Fine-tuned a Custom OCR Model"
        }
    ];

    // Add Certifications Data
    const certifications = [
        {
            title: "Fundamentals of MCP",
            issuer: "Hugging Face",
            date: "2024",
            link: "https://drive.google.com/file/d/1czVQsVSKyvkJpmyNjsa0I2d861IjdvKk/view?usp=sharing"
        },
        {
            title: "LLM",
            issuer: "Hugging Face",
            date: "2025",
            link: "https://drive.google.com/file/d/1VKH7Enj34OHoI9K27NFKovIxacDqoxSj/view?usp=sharing"
        },
        {
            title: "AI Agents Fundamentals",
            issuer: "Hugging Face",
            date: "2025",
            link: "https://drive.google.com/file/d/1QndLNzEzg7N0CpUxgYWBhqXDPOdXOcQe/view?usp=sharing"
        },
        {
            title: "Advanced Learning Algorithms",
            issuer: "Coursera",
            date: "2024",
            link: "https://www.coursera.org/account/accomplishments/verify/8ALUPZRDWUNY"
        },
        {
            title: "ML: Regression and Classification",
            issuer: "Coursera",
            date: "2024",
            link: "https://www.coursera.org/account/accomplishments/verify/WKVBV7H58XPA"
        }
    ];

    // Populate Experience
    const experienceTimeline = document.querySelector('.experience-timeline');
    experience.forEach(exp => {
        const div = document.createElement('div');
        div.className = 'experience-item';
        div.innerHTML = `
            <h3>${exp.title}</h3>
            <div class="experience-company">${exp.company}</div>
            <div class="experience-dates">${exp.dates}</div>
            <div class="experience-description">${exp.description}</div>
        `;
        experienceTimeline.appendChild(div);
    });
    // Populate Certifications
    const certsGrid = document.querySelector('.certifications-grid');
    certifications.forEach(cert => {
        const div = document.createElement('div');
        div.className = 'certification-card';
        div.innerHTML = `
            <h3><a href="${cert.link}" target="_blank">${cert.title}</a></h3>
            <p>${cert.issuer}</p>
            <div class="cert-date">${cert.date}</div>
        `;
        certsGrid.appendChild(div);
    });

    // Rest of previous JavaScript code remains the same
});
document.addEventListener('DOMContentLoaded', () => {
    // Animated Background
    const canvas = document.getElementById('techBg');
    const ctx = canvas.getContext('2d');
    
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    class Particle {
        constructor() {
            this.reset();
        }
        
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2;
            this.speed = Math.random() * 0.5 + 0.1;
            this.angle = Math.random() * Math.PI * 2;
        }
        
        update() {
            this.x += Math.cos(this.angle) * this.speed;
            this.y += Math.sin(this.angle) * this.speed;
            
            if (this.x < 0 || this.x > canvas.width || 
                this.y < 0 || this.y > canvas.height) {
                this.reset();
            }
        }
        
        draw() {
            ctx.fillStyle = 'rgba(35,134,54,0.3)';
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    const particles = Array(100).fill().map(() => new Particle());
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            p.update();
            p.draw();
        });
        requestAnimationFrame(animate);
    }
    
    resizeCanvas();
    animate();
    window.addEventListener('resize', resizeCanvas);

    // Dynamic Content
    const skills = [
        'Python', 'TensorFlow', 'PyTorch', 'FastAPI', 'Flask', 'JavaScript', 'PHP', 'MLops',
        'Laravel', 'Streamlit', 'Shell Scripting', 'Vue.js', 'Spring Boot', 'HTML', 'CSS', 'Tailwind CSS', 'Docker', 'Google Cloud Platform', 'LangChain','LangGraph',
        'NLP','Computer Vision' ,'Deep Learning', 'Deep Reinforcement Learning', 'LLM', 'Linux',
        'Git', 'Machine Learning', 'PERT', 'OCR', 'Object Detection', 'Object Classification',
        'Web Development',
    ];

    const projects = [
         {
            id: 'ducucite',
            title: 'DocuCite-Agent',
            description: `
                <ul class="">
                    <li>Built a MCP(model context protocol) server that allows users to upload documents and interact with an AI agent that can answer any question based on the uploaded content. Each response includes precise references (page and paragraph number) to the original document, ensuring transparency and easy verification.
                    </li>
                    <video controls style="width: 100%; height: auto; margin-top: 10px;">
                    Demo
                    <source src="https://github.com/user-attachments/assets/79a804bb-2560-42b8-9a41-bbdc8da0832b">
                    </video>
                </ul>

            `,
            tech: 'Python, LLM, RAG, MCP, Deep Learning, Fine Tuning, LangChain, PERT, Git'
        },
        {
            id: 'academic-chatbot',
            title: 'Academic Chatbot',
            description: `
                <ul class="">
                    <li>Conducted a comparative study of two chatbot development approaches: fine-tuning and Retrieval-Augmented Generation (RAG).</li>
                    <li>Fine-tuned the pre-trained Llama 3.1 8B language model using UnSloth and LoRA, specifically optimized to assist international students by leveraging a custom academic dataset.</li>
                    <li>Developed and implemented a robust RAG system that combines the Llama 3.1 8B model with a hybrid retrieval mechanism using BM25 and embedding model with reranker(BGE-M3 with BGE-Reranker).</li>
                    <li>The dataset included comprehensive information such as:
                        <ul class="sublist">
                            <li>Housing and rental options for students.</li>
                            <li>Study and work conditions for international learners.</li>
                            <li>Detailed descriptions of courses, curricula, and academic requirements in the Department of Informatics and Artificial Intelligence.</li>
                        </ul>
                    </li>
                    <video controls style="width: 100%; height: auto; margin-top: 10px;">
                    Demo
                    <source src="https://github.com/user-attachments/assets/3ba61ac0-f84b-45bf-babd-4988ba909a1e">
                    </video>
                </ul>

            `,
            tech: 'Python, LLM, RAG, PyTorch, Deep Learning, Fine Tuning, LangChain, PERT, Git'
        },
        {
            id: 'object-detection',
            title: 'Application of the LoRA on Object Detection model',
            description: `
                <ul>
                    <li>This research project was conducted in collaboration with a PhD student from Sorbonne University. The objective was to explore the application of LoRA (Low-Rank Adaptation) to enhance the performance of DiffusionDet, an object detection model, under few-shot learning conditions. The goal was to evaluate whether LoRA can effectively adapt the model to new object categories using limited annotated data, improving efficiency and generalization in low-resource scenarios.</li>
                    <li>We applied this approach to aerial imagery datasets, specifically DOTA (Dataset for Object Detection in Aerial Images) and DIOR (Dataset for Object Recognition in Aerial Images). These datasets contain complex scenes with multiple object classes captured from aerial perspectives, making them ideal for evaluating few-shot object detection in real-world scenarios.
                    </li>
                    <li>The paper can be found here: <a href="https://arxiv.org/abs/2504.06330">https://arxiv.org/abs/2504.06330</a></li>
                </ul>
            `,
            tech: 'Python, PyTorch, Transformer, LoRA, Git'
        },
        {
            id: 'ocr',
            title: 'Handwritten Text Recognition with Fine-Tuned TrOCR',
            description: `
                <ul>
                    <li>This project fine-tunes the microsoft/trocr-large-handwritten model from Hugging Face for handwritten text recognition on a custom dataset. The goal is to adapt the model to recognize specific handwritten text styles or domains with improved accuracy.
                    </li>
                    <video controls style="width: 100%; height: auto; margin-top: 10px;">
                    Demo
                    <source src="https://github.com/user-attachments/assets/9c08b124-290e-45eb-88f7-775e8118e7c6">
                    </video>
                </ul>
            `,
            tech: 'Python, PyTorch, Transformer, LoRA, Git'
        },
        {
            id: 'object-classification',
            title: 'Object classification',
            description: `<ul>
                <li>
                    Trained a MobileViT model on the SPOTS-10: Animal Pattern dataset to classify animals based on their body patterns and textures, and on the CIFAR-10 dataset to classify objects. Developed an API using FastAPI, deployed the model trained on CIFAR-10 with Docker on Google Cloud Platform, and created a user interface hosted on Streamlit Community Cloud.
                </li>
                
                    <video controls style="width: 100%; height: auto; margin-top: 10px;">
                    Demo
                    <source src="https://github.com/user-attachments/assets/ae1c0d9a-5c9c-4c3d-885f-fecacd865b87">
                    </video>
            </ul>`,
            
            
            tech: 'Python, PyTorch, Git, Google Cloud Platform, FastAPI, Docker, Streamlit'
        },
        {
            id: 'asr',
            title: 'Automatic Speech Recognition (ASR)',
            description: `
                <ul class="">
                    <li>Developed and fine-tuned the Whisper Automatic Speech Recognition (ASR) model using the PolyAI/minds14 dataset to enhance performance for speech-to-text applications.</li>
                </ul>
            `,
            tech: 'Python, PyTorch, Deep Learning, Fine Tuning, Transformers'
        },
        {
            id: 'handmotion-prediction',
            title: 'HandMotion Prediction',
            description: 'Developing a machine learning project to predict the acceleration of patients hands, providing one prediction per second for each hand from 7 AM to 7 PM. The dataset contains acceleration values (x, y, z) for both hands and corresponding timestamps, with 50 data points recorded per second. Responsibilities include synchronizing datasets for both hands by aligning timestamps, handling missing data through linear interpolation, and training a Long Short-Term Memory (LSTM) model to produce accurate, second-level predictions.',
            tech: 'Python, Data Analysis, PyTorch, Time-series, Git'
        },
        {
            id: 'e-commerce',
            title: 'E-Commerce Web application',
            description: `Developed a web application for sports shoe sales using a Vue.js frontend and a Laravel backend. The frontend, built with Vue.js, provided a dynamic and responsive user interface, enabling users to browse products, filter by size, brand, and category, and manage their shopping cart in real time. The backend, powered by Laravel, handled key functionalities such as user authentication, product management, inventory tracking, order processing, and payment integration. The system also included an admin dashboard for managing product listings, viewing sales analytics, and handling customer queries. The application aimed to deliver a seamless e-commerce experience optimized for both desktop and mobile users.`,
            tech: 'Java script, PHP, Vue.js, Laravel, HTML, CSS, Tailwind, Git'
        },
        {
            id: 'cafe-system',
            title: 'Café System',
            description: `Developed a Point of Sale (POS) management system for a café using Java and the Spring Boot backend framework. The system was designed to streamline daily operations by managing orders, inventory, tables, billing, and staff roles. Key features included real-time order tracking, digital receipts, menu management, and role-based access for cashiers and administrators. The backend was built with Spring Boot to ensure scalability, modularity, and efficient API handling. The application aimed to improve service speed, reduce human error, and provide insightful sales reports for business analysis.`,
            tech: 'Java, Spring Boot, HTML, CSS, Tailwind, Java script ,Git'
        },
        {
            id: 'air-writing',
            title: 'Air Writing',
            description: `Collected and prepared khmer dataset to train and fine-tune an existing machine learning model with the goal of improving its prediction accuracy. The process involved data cleaning, augmentation, and labeling to ensure high-quality input. The model was retrained using the updated dataset, followed by performance evaluation through metrics such as accuracy, precision, recall, and F1-score. This iterative process helped enhance the model’s generalization and reliability in real-world scenarios.`,
            tech: 'Python, PyTorch ,Git'
        },
    ];

    

    // Populate Skills
    const skillsGrid = document.querySelector('.skills-grid');
    skills.forEach(skill => {
        const div = document.createElement('div');
        div.className = 'skill-card';
        div.textContent = skill;
        skillsGrid.appendChild(div);
    });

    // Populate Projects
    const projectsGrid = document.querySelector('.projects-grid');
    projects.forEach(project => {
        const div = document.createElement('div');
        div.className = 'project-card';
        div.id = project.id;
        div.innerHTML = `
            <h3>${project.title}</h3>
            <p>${project.description}</p>
            <div class="tech">${project.tech}</div>
        `;
        projectsGrid.appendChild(div);
    });

    // Check for anchor link on page load
    window.addEventListener('DOMContentLoaded', () => {
        const hash = window.location.hash.substring(1); // Get #id from URL
        if (hash) {
            const project = document.getElementById(hash);
            if (project) {
                project.scrollIntoView({ behavior: 'smooth' });
                project.style.backgroundColor = '#f8f9fa'; // Optional highlight
            }
        }
    });

    // Mobile Menu
    const menuBtn = document.querySelector('.menu-btn');
    const navLinks = document.querySelector('.nav-links');
    
    menuBtn.addEventListener('click', () => {
        navLinks.style.display = navLinks.style.display === 'flex' ? 'none' : 'flex';
    });

    // Smooth Scroll
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});

// script.js
// Add education data
const education = [
    {
        degree: "MSc in Artificial Intelligence and Data Science",
        institution: "IMT Mines Ales",
        dates: "2023 - 2025",
        details: ""
    },
    {
        degree: "BSc in Computer Science",
        institution: "Institute of Technology of Cambodia",
        dates: "2019 - 2023",
        details: ""
    }
];

// Populate Education
const educationTimeline = document.querySelector('.education-timeline');
education.forEach(edu => {
    const div = document.createElement('div');
    div.className = 'education-item';
    div.innerHTML = `
        <h3>${edu.degree}</h3>
        <div class="education-institution">${edu.institution}</div>
        <div class="education-dates">${edu.dates}</div>
        <p class="education-details">${edu.details}</p>
    `;
    educationTimeline.appendChild(div);
});