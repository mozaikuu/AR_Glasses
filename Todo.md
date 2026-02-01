# Rules

- ### **NEVER PUSH CODE TO "MAIN" OR "PROJECT DIVERGENCE"**
- Only pick one task at a time
- Do NOT fuck up the folder structure (it is fragile as it is)
- Always comment next to code
- Do not delete tasks that are done
- Always add tasks followed by your name and a question mark in the **Suggestions** section
- Always add tasks in order of urgency
- If multiple people are assigned the same task then order people by amount of work done
- When task is done add a checked box in the beginning
- Add your name next to the task you assigned yourself and do not assign yourself multiple tasks for the future. (no dibs)
- Do not mindlessly use AI
- > Always try to do at least two tasks a week

### Urgent:

run all 3 previous unfinished tasks and fix all errors

- [ ] docs
   - [ ] requirements
   - [ ] prototype
   - [ ] expectations
   - [ ] comparison
   - [ ] files
      - [ ] 4 pdf
      - [ ] 1 word
      - [ ] 1 img
      - [ ] multiple diagrams
      - [ ] sandy file
      - [ ] sandy chat
- [ ] Presentation
- [ ] Code: DT_GB_148

### Abstract goals:

- [ ] streamlit / flask
- [ ] mobile test
- [ ] fix nova
- [ ] migrate to notion
- [ ] hardware start
- [ ] navigation start

### Current goal:

- [ ] _Navigation_

### Test & Fix

- [ ] model satisfaction
- [ ] Overthinking
- [ ] investigate how the model sees its own chain of thought
- [ ] desync between tool use and model recall
- [ ] camera permissions murky
- [ ] investigate formatting (json)
- [ ] in case of refusal it should break the loop
- [ ] reimplement chain of thought
- [ ] try same output 10 times?
- [ ] is ans actually tall cool output or is it hallucinations?
- [ ] is model stable?
- [ ] are tools active?
- [ ] is history running correctly?
- [ ] generalize pathing
      ~~~ take me from 46 to dean
      🤖 AI Assistant:

                       Please choose a valid start location from the following: Entrance, Hall 2-0-25, Hall 2-0-16, Stairs G, Elevator G, Floor 1, Left Corridor, Elevator F1, TA Office, Section 2-1-52, Hall 2-1-45, Section 2-1-41, Right Corridor, Hall 2-1-76, Hall 2-1-77, Hall 2-1-83, Hall 2-1-84 ~~~

            take me from 2-1-45 to dean
            🤖 AI Assistant:

                  Action already taken.

- [ ] reset history due to task conflicts

# Todo:

- [ ] fix todo
- [ ] Architechture, Refactor and Design freeze
- [ ] Tech debt list
- [ ] module boundaries and interfaces
- [ ] system arch diagram
- [ ] Unit testing
   - [ ] Tools
      - [ ] stt
      - [ ] tts
      - [ ] nova wakeword
      - [ ] vision detect
      - [ ] search web
   - [ ] mcp
   - [ ] server
   - [ ] gateway
   - [ ] streamlit -> flask
   - [ ] api
   - [ ] agent
   - [ ] llm
   - [ ] modes
   - [ ] config
   - [ ] free llm api sources & model picker based on task
   - [ ] notion documentation
   - [ ] mobile permissions
   - [ ] utils
   - [ ] review Review
   - [ ] remove redundant files
- [ ]
- [ ] try out Clawdbot
- [ ] try out Qwen TTS
- [ ]  - [ ] Navigation
   - [ ] Augmented reality
   - [ ] Graph Theory
   - [ ] MCP Tool use
- [ ] Harware?
   - [ ] Etching
      - [ ] Chem
         - [ ] Items

---

# 3 month plan with ChatGPT 5.2

🗓️ 3-Month Timeline (12 Weeks)
🔵 MONTH 1 — Foundations & Design (Weeks 1–4)
🎯 Goal

- Freeze architecture, design navigation logic, and design PCB before touching hardware.

- Week 1 — Requirements Freeze & Architecture Lock
   - Navigation (Software)
      - Tasks
         - Decide navigation scope:
            - Indoor only (recommended)
            - Floor-based graph navigation (rooms, corridors, stairs)
         - Define AR output:
            - Arrows
            - Direction text (“Turn left”)
            - Distance indicator
      - Deliverables
         - Indoor map as JSON graph
         - Defined navigation states:
            - Idle
            - Navigating
            - Re-routing
            - Destination reached
- 📌 Judges care that scope is frozen.
   - Hardware
   - Tasks
      - Finalize components:
         - MCU: ESP32-S3 (recommended for camera + AI streaming)
         - Camera: OV2640 / OV5640
         - IMU: MPU6050 or ICM-20948
         - Mic: I2S MEMS mic (INMP441)
         - Power: LiPo + TP4056 or PMIC
         - HUD: Micro-OLED or LED waveguide (prototype)
      - Deliverables
         - Block diagram
         - Component list with datasheets

- Week 2 — Navigation Logic + PCB Schematic
   - Navigation
      - Tasks
         - Implement A\* on indoor graph
         - Input: current node + destination
         - Output: list of waypoints
      - Deliverables
         - Working A\* algorithm
         - Test cases:
            - Same floor
            - Multi-corridor
            - Stair navigation
- 📌 Judges LOVE algorithms + test cases.
   - Hardware
      - Tasks
         - Draw schematic in KiCad / EasyEDA:
            - ESP32
            - Camera interface
            - Mic (I2S)
            - IMU (I2C)
            - Power management
         - Deliverables
            - Schematic PDF
            - Netlist ready for PCB
   - 📌 This proves engineering rigor.

- Week 3 — AR Overlay + PCB Layout
   - Navigation + AR
      - Tasks
         - Convert waypoints → AR arrows
         - Align arrows with:
            - IMU heading
            - User orientation
         - Deliverables
            - AR mockup images
            - Demo video (even on phone screen)
- 📌 AR doesn’t need to be perfect — visible logic is enough.
   - Hardware
      - Tasks
         - PCB layout:
            - 2-layer PCB (cost-effective)
            - SMD footprints
            - Short signal paths for camera + mic
         - Deliverables
            - PCB Gerber files
            - 3D PCB render
- 📌 3D render = instant credibility.

- Week 4 — Design Review & Order PCBs
   - Combined
      - Tasks
         - Review:
            - Power integrity
            - Signal routing
            - Component spacing
         - Deliverables
            - Final Gerbers sent to manufacturer
            - BOM (Bill of Materials)
- 📌 Judges see this as “industry workflow”.

- 🟠 MONTH 2 — Implementation & Assembly (Weeks 5–8)
- 🎯 Goal
- Get real hardware running + navigation logic integrated.

- Week 5 — Navigation Integration & PCB Arrival
   - Navigation
      - Tasks
         - Integrate navigation with:
            - LLM intent parser
            - Voice commands (“Take me to…”)
         - Deliverables
            - End-to-end navigation demo
            - Logs of commands → path → output
      - Hardware
         - Tasks
            - Receive PCBs
            - Inspect visually
            - Prepare soldering tools:
               - Hot air gun
               - Flux
               - Microscope

- Week 6 — SMD Soldering & Power-Up
   - Hardware
      - Tasks
         - Solder:
            - Power circuit FIRST
            - ESP32
            - Camera
            - IMU
            - Mic
         - Deliverables
            - Power test (no overheating)
            - ESP32 boots successfully
- 📌 FIRST BOOT VIDEO = huge win.

- Week 7 — Firmware + Sensor Testing
   - Hardware
      - Tasks
         - Flash firmware
         - Test:
            - Camera streaming
            - Mic recording
            - IMU orientation
         - Deliverables
            - Sensor data logs
            - Demo: head rotation → IMU values
         - Navigation
            - Tasks
               - Real-time heading correction
               - Re-route when user deviates
            - Deliverables
               - Demo video of re-routing

- Week 8 — AR + Hardware Integration
   - Combined
      - Tasks
         - Stream sensor data to backend
         - Receive navigation instructions
         - Display AR arrows
      - Deliverables
         - Live demo:
            - Speak destination
            - See arrows
            - Hear guidance
- 📌 This is the core demo.

- 🟢 MONTH 3 — Testing, Optimization & Presentation (Weeks 9–12)
- 🎯 Goal
- Stability, evaluation, and judge-proof documentation.

- Week 9 — System Testing
   - Tasks
      - Navigation accuracy tests
      - Latency measurements
      - Battery consumption analysis
   - Deliverables
      - Metrics table
      - Graphs (latency vs distance)

- Week 10 — Failure Cases & Safety
   - Tasks
      - Test:
         - Sensor loss
         - Network delay
         - Wrong map
      - Deliverables
         - “What happens if…” slide
         - Graceful degradation logic
- 📌 Judges love safety awareness.

- Week 11 — Documentation & Diagrams
   - Tasks
      - Finalize:
         - Architecture diagram
         - Navigation flow
         - Hardware PCB photos
         - Assembly steps
      - Deliverables
         - Final report sections
         - High-quality images

- Week 12 — Demo Polish & Defense Prep
   - Tasks
      - Rehearse demo
      - Prepare Q&A answers
      - Create backup videos
   - Deliverables
      - 2-minute demo
      - 5-minute technical explanation

- 📌 What You MUST Show Judges
- Area Proof
- Navigation Graph + A\* + AR demo
- Hardware PCB + SMD + boot
- Integration Voice → AR path
- Engineering Schematics + Gerbers
- Evaluation Metrics + limitations
- ⚠️ Critical Advice (Listen Carefully)
- Do NOT over-engineer AR optics
- Do NOT redesign PCB mid-way
- Do NOT chase SLAM unless time remains
- This plan is ambitious but realistic.

---

- Make it work with a free api
- fix text
- fix audio and increase its accuracy

- [ ] Restructure todo using nesting and Priority
- [ ] Clean up Repo by removing unnecessary files

- [ ] Features
   - [ ] Indoor Navigation
   - [ ] Speech to Text
   - [x] Computer Vision
   - [ ] Text to speech
   - [x] search the web
   - [ ] Take Notes (Tool)

- [ ] Capture audio (Streamlit)
- [ ] Capture Frame (Streamlit)
- [x] Capture text (Streamlit)
- [ ] Gyroscope Gps Orientation
- [ ] Review old tasks
- [ ] Buy Hardware
- ~~[x] Streamlit~~
- ~~[x] Mcp Server Test~~
- ~~[x] Client test~~
- [x] Gateway test
- [ ] show response on phone
- [ ] add more tools + ideas
- [ ] AR Experience
- [ ] When the model runs for too long the gateway disconnects and needs a restart from streamlit to reconnect
- [ ] Review My code for more Fixes/ideas/documentation
- [ ] audio and video are broken
- [ ] Test Different Models
- [ ] Choose the least busy path (Postponed)
- [ ] img to real life mapping (Postponed)
- [x] add thinking speeds
- [ ] switch to Online LLMs
- [ ] Eye Tracking (Postponed)
- [ ] Docker/Onnx/Sdk/.EXE
- [ ] Hololens EMULATOR (Postponed)
- [ ] Our Hardware
- [ ] Fully Agentic (Postponed)
- [ ] Try Projector
- [ ] Try Piece of Screen
- [ ] Try Arduino?
- [ ] Avatar AR (Postponed)
- [ ] MQTT + Ngrok
- [ ] Database
- [ ] 3D-Mesh/Measure Building somehow (Postponed)
- [ ] 2D Map of Building
- [ ] Vuforia
- [ ] Postman Problem
- [ ] Response takes too much time... (HPC?)
- [ ] audio/img do not refresh between prompts
- [ ] camera is blue??
- [ ] make everything automatic
- [x] todo + rules
- [ ] Hardware
   - [ ] Glasses Design
   - [ ] Parts
- [ ] Notion
- [ ] Ngrok / MQTT

---

- Suggestions:
   - add something idk

# TODO: Make this a checkbox section

---

# Competition

- [ ] impact on society/industry specially telecommunication sector
- [ ] clarity and validity of objectives
- [ ] originality
- [ ] writing and presentation quality
- [ ] completing ALL the required fields
- [ ] grammar and language
- [ ] references are correct
- [ ] PROJECT DESCRIPTION
   - [ ] OVERVIEW
      - [ ] (i) Problem definition
      - [ ] (ii) approach and tools/techniques
      - [ ] (iii) overview of system modules
      - Use block diagrams and figures to describe your ideas. Be as clear as possible about the ideas in order to show the reviewer the value of your idea.
   - [ ] IMPACT
      - [ ] Why do you consider this project?
      - [ ] What is its impact on community/market/end user/… specially telecommunication sector?
   - [ ] NOVELTY AND FEATURES
      - [ ] Explain
         - [ ] (i) novelty
         - [ ] (ii) features
         - [ ] (iii) related products
   - [ ] DELIVERABLES
      - [ ] What is the project final outcome (HW device, SW package, simulation ...)?
      - It is important to clearly identify the final outcomes supported by evidence and results.
   - [ ] BUSINESS PLAN AND MARKET ANALYSIS
      - [ ] Market research
         - [ ] product national or multinational
         - [ ] business opportunities
         - [ ] niche added value.
         - [ ] potential market for your project?
         - [ ] Do you expect any demand on the final product?
   - [ ] Project EXPENSES
      - [ ] List:
         - [ ] equipment
         - [ ] tools
         - [ ] modules
         - [ ] components
         - [ ] software
         - [ ] …
         - [ ] Item
         - [ ] Type
         - [ ] (Hardware/ Software/ Other)
         - [ ] Specifications, (brief description)
         - [ ] Cost (LE.)
         - [ ] Total Project Cost

---

# Final

• Project Requirements
 Project Contents
Students should work on preparing power point slides include the following:

- Problem Overview
- Introduction and Motivations
- Project Goals
- Previous/Related Projects
- Requirements Analysis
- System Design Models:
  o For Software Projects: May include some or all of the following:
  ▪ Class Responsibility Collaborator (CRC) Cards
  ▪ Flowchart Diagrams
  ▪ UML diagrams (Uses Cases/Class Diagram/ Component Diagram …etc.)
  ▪ System Components and Architectural Diagrams
  ▪ DFD Diagrams
  ▪ Database Diagrams (Schema, ER-Diagram)
  ▪ Deployment Diagram
  ▪ Package Diagram
  ▪ UI sketches
  o For Hardware Projects: May include some or all of the following:
  ▪ Block Diagram
  ▪ Circuit Diagrams/Schematic diagrams
  ▪ Pin diagram
  ▪ Timing diagram
  ▪ Flowchart
  ▪ State Diagram
  ▪ PCB Layout Diagram
  ▪ System Architecture Diagram
  ▪ Data Flow Diagram
  ▪ Power Distribution Diagram
- Used Technologies and tools
- Time Plan (Project -1 only)
- Business Plan
- Roles of Team Members
- Prototype Implementation (Mandatory for Project -2, Optional for Project-1)
- Results/Testing and Outcomes
- Conclusions and future Works
- References
  • Presentation
   Innovative slides that summarize the project contents in 20 minutes and it is built with the following
  features:
  o Contents Features:
  ▪ Focused: focus on what you did and why it matters
  ▪ Clear Contribution: what you built or proved
  ▪ Emphasize results: what you achieved and how it was validated
  o Appearance Features
  ▪ Consistent Theme: Use a clean, professional template
  ▪ Readable Fonts: Use large font (min 24pt), clear contrast
  ▪ Minimal Text: Avoid paragraphs—use bullets
  ▪ Visuals: Add diagrams, charts, images where possible
  ▪ Code/Math: Use readable formatting or screenshots
   Delivery of the presentation should be managed well by the team members and follow the following
  tips:
  ▪ Divide the presentation into logical sections (e.g., Intro, Design, Implementation,
  Results).
  ▪ Ensure equal participation so everyone speaks.
  ▪ Assign each section based on team members’ strengths and contributions.
  ▪ Practice how you’ll hand over to each other. For example:
  “Now my teammate [Name] will explain the system architecture.”
  ▪ Avoid awkward pauses or interruptions.
  ▪ Know each other’s parts well enough to back each other up if needed.
  ▪ Use the same terminology, tone, and pace.
  ▪ Make sure everyone follows the same slide format and presentation style (don’t mix
  formal and casual tones).
  ▪ Respect time limits (15–20 minutes is common)
  ▪ Have someone track time and make adjustments if needed.
  ▪ Practice together timing
  ▪ Speak clearly and confidently
  ▪ Don't read slides—explain them
  ▪ Prepare for possible questions
  ▪ Agree in advance who will answer which types of questions.
  ▪ If a question is more relevant to another member, pass it politely:
  ▪ Pay attention to teammates when they’re speaking—don’t look disengaged
  ▪ Don’t talk among yourselves or check your phone.
  • Documentation
- Use the approved NMU-CSE Graduation Project Template
- Final documentation must be submitted 2days before the date of the final Discussion
  (To be announced later)
- Document Format: It must be submitted as both:
  o A soft copy: Must be submitted on a CD/ROM or a flash memory stick to the Dean
  Office and it must contain:
  ▪ MS Word or PDF of the project documentation contents
  ▪ Source code files (in a ZIP folder) [Project 2 only]
  ▪ Project presentation slides (PPT or PDF)
  ▪ Any supplementary materials (e.g., datasets, user manuals)
  o A Printed Hard Copy: Must be submitted to the Dean office as Hard Leather-bound
  documentation (5 – Copies).
- The cover should have:
  ▪ A logo for both NMU and CSE in addition to an optional logo for the project
  ▪ An academic title of the project with an optional commercial title.
  ▪ The name of the main supervisor and the assistants
  ▪ The names of the team members
  ▪ The Academic Graduation Year
  Poster (Pose) Preparation Instructions (Optional-Project 2 only)
  a. Size and Orientation
  •
  Standard Size: A1 (594 mm × 841 mm) or A0 (841 mm × 1189 mm)
  •
  Orientation: Preferably portrait unless otherwise specified
  🧱 b. Recommended Poster Structure
  Section
  Description
  Title
  Large, bold project title at the top
  Student Info
  Names, ID numbers, department, supervisor
  Introduction
  Problem background, motivation
  Objectives
  Clear goals of the project
  Methodology
  Brief system design, tools, architecture diagram
  Implementation
  Screenshots, circuit images, block diagram
  Results
  Graphs, sample outputs, testing outcomes
  Conclusion & Future Work Summary and possible improvements
  QR Code (Optional)
  Link to full documentation or demo video
  🎨 c. Design Tips
  •
  Use simple, professional colors (white background is best)
  •
  Use bullet points, not paragraphs
  •
  Use large fonts (24 pt for text, 36–48 pt for titles)
  •
  Include visuals: diagrams, flowcharts, screenshots, photos
  •
  Avoid clutter—leave white space for easy reading
  🏳️ 2. Banner Preparation Instructions (Optional – Project 2 only)
  📐 a. Size
  •
  Typical banner size:
  Width: 1.5 to 2 meters
  Height: 0.5 to 0.75 meters
  (Check showroom display stand size before printing)
  📋 b. Content to Include
  •
  Project title (centered, large font)
  •
  Student(s) name(s) and ID(s)
  •
  Supervisor’s name
  •
  University, department logo (left)
  •
  Year or session (right)
  •
  Optional slogan or one-line project summary
  🎨 c. Banner Design Tips
  •
  Use contrasting colors for visibility
  •
  Ensure all text is readable from a distance
  •
  Keep it minimal and bold
  •
  Use vector graphics or high-resolution images only
  📍 3. Printing and Setup
  •
  Use high-resolution PDF format for printing
  •
  Test print a small version to check layout and clarity
  •
  Mount the poster on a foam board or easel if required
  •
  Hang or place the banner above or near your display table
  📷 4. Bonus Tips for Display Day
  •
  Wear professional or project-branded attire
  •
  Place a laptop/device for demo next to your poster
  •
  Bring extra handouts or business cards (optional)
  •
  Be ready with a 1-minute verbal pitch for visitors

---

- [x] Slide 1: Title SlideProject Name (e.g., "VisionAgent: Context-Aware Wearable Intelligence").Your name, supervisor, and institution.
- [x] Slide 2: The Problem StatementFocus on "Cognitive Overload" or "Information Friction." Why is pulling out a phone inefficient for real-time tasks?
- [x] Slide 3: The Solution (The "Agentic" Angle)Define what makes your glasses different from standard AR. Emphasis on proactive vs. reactive assistance (the glasses understand what you are doing before you ask).Part 2: Technical Architecture
- [x] Slide 4: System Overview (High-Level)A block diagram showing the flow: Sensors (Input) → Perception (AI) → Action (Output).
- [x] Slide 5: Hardware SpecificationsComponents: Camera, Microphone, Bone Conduction Audio, Micro-controller (ESP32-S3, Raspberry Pi CM4, etc.), and Battery.
- [x] Slide 6: The Software Stack & AI PipelineVision: (e.g., YOLO, CLIP, or GPT-4o-vision) for object recognition.LLM/Agent: The "Brain" (e.g., LangChain or AutoGPT) that manages memory and task planning.Context Engine: How the glasses store "short-term memory" of what they've seen.
- [x] Slide 7: Multimodal InteractionHow the user interacts: Voice, gesture, or gaze.Part 3: Business & Strategy (As Requested)
- [ ] Slide 8: Business Model Canvas (BMC)You should present this as a clear table. Key sections to highlight:Value Proposition: "Eyes-free, hands-free context-aware intelligence."Customer Segments: Industrial workers, the visually impaired, or tech early-adopters.Revenue Streams: Hardware sales + "AI-as-a-Service" subscription.
- [ ] Slide 9: Market Analysis & CompetitorsA comparison table: Meta Ray-Bans (No display/limited agent) vs. Apple Vision Pro (Too bulky) vs. Your Project (The middle ground).
- [x] Slide 10: Target Use CasesScenario A: Assisted repair (identifying tools/parts).Scenario B: Social/Accessibility (reading menus, recognizing faces for the blind).Part 4: Implementation & Results
- [ ] Slide 11: The Prototype (Physical)Photos of your actual build. Highlight the 3D printing or assembly process.
- [ ] Slide 12: Testing & Performance DataLatency (How fast does the agent respond?), Accuracy of object recognition, and Battery life.
- [ ] Slide 13: Ethical Considerations & PrivacyCrucial for this topic: How do you handle the "always-on" camera? Data encryption and the "Privacy LED" indicator.Part 5: Conclusion
- [ ] Slide 14: Future RoadmapMiniaturization, integration with Prescription lenses, and local "On-Device" processing to reduce cloud reliance.
- [ ] Slide 15: Conclusion & Key TakeawaysSummarize the impact of agentic wearables.
- [ ] Slide 16: Q&A / ReferencesSuggested Business Model Canvas (Quick Reference)Key PartnersKey ActivitiesValue PropositionsCustomer RelationshipsCustomer SegmentsAI Providers (OpenAI/Google), Lens ManufacturersSoftware Dev, Hardware DesignHands-free real-time problem solvingSubscription-based updatesField Engineers, Visually Impaired, StudentsKey ResourcesChannelsCost StructureRevenue StreamsProprietary AI Agents, SensorsDirect-to-Consumer, Enterprise TechR&D, Manufacturing, Cloud Server costsUnit Sales, Pro-AI SubscriptionTechnical Must-Haves for your Presentation:A Video Demo: Since "Agentic" behavior is hard to explain, show a 60-second clip of the glasses identifying an object and giving advice without being prompted.The "Failure"
- [ ] Slide: Judges love to see what went wrong and how you fixed it. It shows engineering maturity.

---

- [ ] better uni logo
- [ ] remove graduation project from title
- [ ] put the faculty name after logo
- [ ] put team logo
- [x] add Supervised by: Associate Professor. Aya Zoghby
- [ ] add New Mansoura, 2025
- [ ] add slogan "SmartVision", "AlexOracle", "OmniVision", "Cerebro"
- [x] fix my name in the file
- [x] ABSTRACT

                Modern wearable technologies aim to enhance human–technology interaction; however, existing smart glasses solutions remain limited in personalization, contextual awareness, and seamless multimodal integration. This paper presents an advanced AI-powered smart glasses system designed to improve daily communication, productivity, accessibility, and decision-making through intelligent, hands-free interaction.
                The proposed system integrates speech recognition, real-time multilingual translation, large language models, computer vision, augmented reality, navigation, and smart home connectivity into a unified wearable platform. A YOLO-based computer vision module enables real-time object detection and face recognition, allowing personalized and context-aware interactions. Indoor navigation is supported through a custom mapping and graph-based routing approach, providing accurate guidance in complex indoor environments.
                Speech input is transcribed using a multilingual automatic speech recognition model and processed by a large language model to understand user intent and generate appropriate responses, which are delivered through natural text-to-speech output. A companion mobile and web platform enables device management, smart home control, accessibility customization, and real-time system monitoring.
                The system is designed with inclusivity as a core principle, supporting users with disabilities through voice-based interaction, visual aids, and hands-free operation, while also enhancing safety and efficiency in daily tasks. Experimental analysis and competitor comparison demonstrate that the proposed solution addresses key limitations of existing smart glasses platforms, particularly in advanced computer vision, indoor navigation, and AI-driven personalization.

- [x] fix bookmarks
- [ ] TABLE OF CONTENTS
- [ ] ABSTRACT
- [ ] 1
- [ ] ACKNOWLEDGEMENTS
- [ ] 2
- [ ] TABLE OF CONTENTS
- [ ] 3
- [ ] LIST OF TABLES
- [ ] 4
- [ ] LIST OF FIGURES
- [ ] 5
- [ ] SYMBOLS & ABBREVIATIONS
- [ ] 6
- [ ]  1.
- [ ] INTRODUCTION
- [ ] 1
- [ ] 1.1.
- [ ] Problem Statement
- [ ] 1
- [ ] 1.2.
- [ ] Project Purpose
- [ ] 2
- [ ] 1.3.
- [ ] Project Scope
- [ ] 3
- [ ] 1.4.
- [ ] Objectives and Success Criteria of the Project
- [ ] 4
- [ ] 1.5.
- [ ] Report Outline
- [ ] 4
- [ ]  2.
- [ ] RELATED WORK
- [ ] 5
- [ ] 2.1.
- [ ] Existing Systems
- [ ] 5
- [ ] 2.2.
- [ ] Overall Problems of Existing Systems
- [ ] 8
- [ ] 2.3.
- [ ] Comparison Between Existing and Proposed Method
- [ ] 10
- [ ]  3.
- [ ] METHODOLOGY
- [ ] 12
- [ ] 3.1.
- [ ] Design Overview
- [ ] 13
- [ ] 3.2.
- [ ] System Architecture
- [ ] 21
- [ ] 3.2.1.
- [ ] Module A
- [ ] 22
- [ ] 3.2.2.
- [ ] Module B
- [ ] 23
- [ ] 3.2.3.
- [ ] Module C
- [ ] 24
- [ ] 3.2.4.
- [ ] Module D
- [ ] 25
- [ ] 3.2.5.
- [ ] Module E
- [ ] 26
- [ ] 3.3.
- [ ] System Software
- [ ] 27
- [ ]  4.
- [ ] EXPERIMENTAL RESULTS
- [ ] 29
- [ ]  5.
- [ ] DISCUSSION
- [ ] 32
- [ ]  6.
- [ ] BUSINESS PLAN
- [ ] 34
- [ ]  7.
- [ ] CONCLUSIONS
- [ ] 39
- [ ] REFERENCES
- [ ] list of tables is wrong
- [ ] change introduction fully
- [ ] fix project purpose
- [ ] label tables and figures appropriately

---

Problem Statement: Cognitive Overload and Information Friction

In modern digital environments, users increasingly rely on smartphones to access information, communicate, and perform real-time tasks. However, the smartphone-centric interaction model introduces significant cognitive overload and information friction, particularly in time-sensitive or attention-critical situations. Cognitive overload occurs when users are required to divide their attention between their physical environment and a digital interface, while information friction refers to the unnecessary effort and delays involved in accessing, navigating, and interpreting information.

Pulling out a smartphone to perform simple tasks—such as checking directions, replying to a message, translating speech, or retrieving contextual information—requires multiple sequential actions: locating the device, unlocking it, navigating through applications, and interpreting visual content. Each step interrupts the user’s current cognitive flow and demands focused visual and motor attention. This process increases mental workload, slows task completion, and raises the likelihood of errors.

In real-time contexts such as navigation, social interaction, learning, or driving, these interruptions are particularly inefficient and potentially unsafe. Users must repeatedly shift attention away from their surroundings, resulting in reduced situational awareness and increased cognitive strain. For individuals with disabilities, high workloads, or complex multitasking demands, this interaction model further exacerbates accessibility challenges.

Despite advances in mobile technology, smartphones remain fundamentally screen-centric and reactive, offering limited contextual awareness and proactive assistance. This creates a gap between the user’s intent and the system’s response, forcing users to actively “pull” information rather than receiving it seamlessly when needed.

Therefore, there is a critical need for an interaction paradigm that minimizes cognitive load and reduces information friction by enabling hands-free, context-aware, and continuous access to information. Addressing this problem requires moving beyond traditional smartphone interfaces toward wearable systems that integrate seamlessly with human perception and real-world activity.

---

This project presents an AI-powered Smart Glasses system designed to enhance daily communication, productivity, accessibility, and indoor navigation. The solution integrates computer vision, speech recognition, large language models, augmented reality, and IoT into a single, low-cost wearable device. Using real-time object detection, multilingual voice interaction (Arabic and English), and AR-based indoor navigation, the system provides hands-free, context-aware assistance in complex indoor environments such as universities, hospitals, and enterprise buildings. By leveraging open-source AI models and affordable hardware, the project delivers an intelligent, scalable, and accessible smart companion that improves user independence, safety, and efficiency while supporting smart building, telecommunication infrastructures and empowering the customer by keeping their data and privacy safe giving them the option of monetizing their own data later down the line. all of that in a one time cost product with no subscriptions unless connected to our cloud for extra services.

---

- Prompts:
   1. always use the venv (Smart_Glasses)
   2. index and read the whole project before changing anything, understand the project and make documentation for it
   3. search_web tool works but visiondetect is seemingly broken
   4. "hey nova" works but it queues and waits for me to do manual record before processing the automatic one when they should be separate
   5. "hey nova" should have the same logic as the manual record
   6. clean up repository of useless files
   7. provide ideas on integrating augmented reality to the project in the form of future work
   8. fix text to speech
   9. streamlit crashes sometimes
   10.   refactor the code if necessary.

Traceback:
pygame-ce 2.5.2 (SDL 2.30.8, Python 3.12.1)
Calibrating microphone...
Microphone calibrated
Wake word detection active. Say 'Nova' or 'Hey Nova' to activate.
Wake word system started
Wake-word system auto-started successfully
Wake-word system is running. State: SystemState.IDLE
Wake word detected: 'nova' (confidence: 1.00)
[MIC] Listening for command...
[CMD] Command received: 'what day is'
WAKEWORD CALLBACK: on_command_received('what day is')

project name
idea companion, nav, modularity, privacy
Target audience
architecture
userflow
comparison table
metrics
Business model canvas

Docs:-

- Acknowledgements ✅
- fix table of contents
- fixed style ✅
- fixed duplication ✅
- fix tables
