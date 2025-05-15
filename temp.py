from context_fusion_tool import ContextFusionTool

internal= [
    "How does the new investment platform align with 1 Finance’s strategic vision and address the market gap left by traditional short-term investment options?",
    "What specific market data and consumer trends support the anticipated ROI and potential for this platform within our target demographic?",
    "Which internal departments and key stakeholders are responsible for the launch, technical integration, and ongoing management of the new investment product?",
    "How has the technology architecture been planned to ensure scalability, operational security, and seamless integration with the existing 1 Finance app?",
    "What measures have been implemented to mitigate risks such as borrower defaults, and how does the platform’s risk diversification strategy operate?",
    "What legal, compliance, and privacy protocols are in place considering that the product is RBI registered and involves direct x-to-x transactions?",
    "What is the detailed timeline for launching the platform, and how have resources been allocated to ensure launch readiness and smooth post-launch operations?",
    "Which performance metrics and KPIs will be used to assess the platform's success, and what future enhancements or additions are planned in its roadmap?"
  ]
external = [
    "What is the new investment platform and how does it enable investors to achieve high returns while diversifying their portfolios?",
    "How does the platform offer flexible investment tenures and what range of investment options (such as lumpsum and SIP) are available?",
    "Who is the target audience for this product, and how does it cater to the financial needs and risk profiles of modern, middle-class investors?",   
    "What steps are involved for a customer to sign up, complete the necessary KYC, and start investing on the platform?",
    "How does 1 Finance ensure that the platform delivers secure, regulated, and transparent x-to-x investment experiences?",
    "What mechanisms are in place to manage risks such as borrower defaults, and how are returns of 10-14% achieved in this context?",
    "How is user data protected and what privacy protocols and regulatory compliances have been established for safe transactions?",
    "How will 1 Finance continue to update and support the platform, and what post-onboarding support can investors expect to receive?"
  ]
tool = ContextFusionTool()
output=tool.run(internal,external,True,"new investment")
print(output)
# from searxng_search import SearxNGTrustedSearchTool

# tool = SearxNGTrustedSearchTool()
# resp = tool.search_with_query("compare PlanMyTax with competitors based on features, pricing, user reviews, and market presence latest data")
# # resp=tool._run(topic="P2P Lending", problem="No formal platform for peer to peer lending", solution="unified platform for all to use simple")
# print(resp)
# from qdrant_tool import kb_qdrant_tool  # Or however your KB tool is exposed
# query = "financial planning centers"
# print(kb_qdrant_tool._run(question=query))

# from web_search import WebTrustedSearchTool
# import os

# tool = WebTrustedSearchTool()
# query = (
#                 "tax planning software competitors"
#         )
# resp=tool._run(query=query)
# print(resp)

# import json
# curr_faq = """{
#   "Title": "1 FINANCE ANNOUNCES THE LAUNCH OF FINANCIAL PLANNING CENTRE TO ENABLE INDIVIDUALS TO OBTAIN PERSONALISED FINANCIAL ADVICE.",
#   "Subtitle": "Dedicated spaces enable deeper personal engagement by merging digital efficiency with the trust of face-to-face advisory.",
#   "IntroParagraph": "[Placeholder Location] - [Placeholder Launch Date] - The Financial Planning Centre represents a groundbreaking shift in financial advisory services. By integrating personalised in-person consultations with expertly crafted sensory experiences, the centre provides an enriching environment designed to instil confidence and promote financial well-being. This innovative approach ensures that clients receive tailored, clear guidance while enjoying a homely ambience that transcends traditional office vibes.",
#   "CustomerProblems": "Many clients feel that purely digital financial advisory lacks the personal connection needed to inspire trust and confidence. The absence of face-to-face interactions often results in miscommunication and uncertainty, leaving clients hesitant to act on important financial decisions. This gap in personalised service leads to a one-size-fits-all approach that fails to address individual financial needs and circumstances.",
#   "Solution": "The Financial Planning Centre addresses these challenges by offering dedicated spaces for in-person consultations with Qualified Financial Advisors. With a structured appointment system and versatile consultation settings – from intimate one-on-one meeting rooms to group environments – the centre provides tailored solutions that cater to each client’s unique financial situation. Enhanced by sensory elements such as music, lighting, and subtle fragrances, this omnichannel strategy successfully bridges the gap between digital convenience and personalised service.",
#   "LeadersQuote": "'We developed the Financial Planning Centre to offer a truly personalised financial advisory experience, ensuring that every client feels genuinely understood and supported in their financial journey.'",
#   "CustomerQuotes": [
#     "I finally feel heard and understood during my consultations.",
#     "This centre’s personal touch has completely transformed my approach to financial planning.",
#     "It’s refreshing to receive expert advice in an environment that feels welcoming and homely."
#   ],
#   "GettingStarted": "To begin, simply register on our website or mobile app and book an available time slot with one of our Qualified Financial Advisors. Experience firsthand a new era of personalised financial planning that seamlessly blends digital accessibility with in-person warmth.",
#   "InternalFAQs": [
#     {
#       "Question": "What is the business rationale behind establishing the Financial Planning Centre?",
#       "Answer": "The Financial Planning Centre was conceived in response to market research indicating that digital-only financial advisory services often miss the personal connection required for trust. By offering dedicated in-person consultations, the Centre addresses the need for authentic, face-to-face engagement, ensuring each client's individuality is respected. Key points include:\n- **Personalisation**: Tailored financial planning based on individual background and needs.\n- **Trust-building**: Direct interaction with Qualified Financial Advisors (QFAs) to foster confidence.\n- **Market Differentiation**: Filling the gap in a sector that has traditionally offered impersonal digital services."
#     },
#     {
#       "Question": "How does the Financial Planning Centre align with 1 Finance's overall strategy?",
#       "Answer": "The Centre aligns strategically by blending digital innovation with personalised financial advisory, reinforcing our commitment to financial well-being. This approach strengthens our omnichannel strategy by:\n- **Enhancing Service Quality**: Marrying technology with human expertise.\n- **Broadening Reach**: Serving high-income individuals in Tier I and Tier II cities.\n- **Sustainable Growth**: Building a scalable model that reflects our long-term vision for comprehensive financial services."
#     },
#     {
#       "Question": "What is the product vision for the Financial Planning Centre?",
#       "Answer": "The vision is to redefine traditional financial advisory by creating a hub that offers a comprehensive and engaging client experience. This vision encompasses:\n- **Innovative Design**: A space that transcends the typical office environment using sensory enhancements like music, lighting, and fragrances.\n- **Personalised Service**: Each consultation is tailored to the financial personality and needs of the individual.\n- **Omnichannel Integration**: Seamless integration of online and in-person engagements for a consistent advisory experience."
#     },
#     {
#       "Question": "What technical approach underpins the Centre's omnichannel integration?",
#       "Answer": "The technical approach ensures that digital interfaces and in-person services are seamlessly integrated. Key components include:\n- **Robust API Frameworks**: To stack digital booking systems with in-person appointment management.\n- **Data Synchronisation**: Real-time updating of client profiles from both digital and physical channels.\n- **User Experience Design**: Streamlined interfaces that simplify both the booking process and in-centre navigation."
#     },
#     {
#       "Question": "What risks have been identified in launching the Financial Planning Centre, and how are they managed?",
#       "Answer": "Several risks have been noted and are mitigated through careful planning:\n- **Operational Risks**: Delays in appointments or mismatches in client expectations are managed by a strict scheduling system.\n- **Technical Risks**: Potential integration issues between digital and in-person systems are addressed with robust internal testing and backup systems.\n- **Market Risks**: Shifts in client preferences are monitored via systematic feedback loops and regular market analysis."
#     },
#     {
#       "Question": "How is scalability ensured given the physical space limitations of the Centre?",
#       "Answer": "Scalability is a core design consideration, managed by:\n- **Flexible Space Allocation**: Different configurations of meeting rooms, pods, and group settings allow adjustments based on demand.\n- **Digital Expansion**: Enhanced online advisory components complement the finite physical capacity.\n- **Phased Rollouts**: Adjusting operational hours and staffing during peak versus off-peak periods ensures efficient utilisation."
#     },
#     {
#       "Question": "What internal roles are critical to the success of the Financial Planning Centre?",
#       "Answer": "Key roles include:\n- **Qualified Financial Advisors (QFAs)**: Frontline personnel interacting directly with clients.\n- **Operational Managers**: Overseeing day-to-day functionalities and ensuring smooth operations.\n- **IT & Systems Specialists**: Guaranteeing seamless digital integration and system security.\n- **Marketing and Communications Teams**: Responsible for both internal updates and public messaging."
#     },
#     {
#       "Question": "Which internal stakeholders are involved in the Centre's launch and operations?",
#       "Answer": "The following stakeholders play crucial roles:\n- **Senior Management**: Providing strategic oversight and funding.\n- **Compliance and Legal Departments**: Ensuring all operations adhere to regulations.\n- **Customer Service Teams**: Handling appointment scheduling and client feedback.\n- **IT Departments**: Managing technology infrastructure and data security."
#     },
#     {
#       "Question": "What legal, compliance, and privacy concerns have been addressed in the design of the Centre?",
#       "Answer": "The Centre is established with a comprehensive focus on legal and compliance aspects:\n- **Data Handling**: Adheres to stringent data protection regulations, ensuring client confidentiality.\n- **Regulatory Compliance**: Meets all financial advisory guidelines and industry standards.\n- **Privacy Measures**: Incorporates secure, private consultation spaces and encrypted digital systems."
#     },
#     {
#       "Question": "How is the safety and privacy of client financial data ensured?",
#       "Answer": "Client data protection is paramount and managed by:\n- **Encryption Protocols**: Implementation of industry-standard encryption for both stored and transmitted data.\n- **Access Controls**: Strict access permissions and audit trails to limit data breaches.\n- **Compliance Audits**: Regular internal and external audits to maintain high security standards."
#     },
#     {
#       "Question": "What is the timeline for the Centre's launch and subsequent operational phases?",
#       "Answer": "The timeline includes several key phases:\n- **Pre-Launch**: Finalising technology integrations, staff training, and marketing rollout.\n- **Launch Phase**: Initial opening to a selected client base to fine-tune processes.\n- **Operational Rollout**: Gradual expansion of services, regular review meetings and feedback integration.\n- **Future Roadmap**: Planned upgrades including digital enhancements and physical expansions."
#     },
#     {
#       "Question": "How are resourcing and budget allocations managed for the Centre?",
#       "Answer": "Resourcing is managed through meticulous planning:\n- **Budget Allocation**: Funds are earmarked for technology, training, and operational expenses.\n- **Staffing Plans**: Detailed schedules ensure that qualified personnel are available during peak hours.\n- **Continuous Monitoring**: Regular reviews and adjustments based on client uptake and feedback."
#     },
#     {
#       "Question": "What key success metrics have been established to evaluate the Centre's performance?",
#       "Answer": "Success will be measured using the following metrics:\n- **Client Satisfaction**: Regular surveys and feedback loops.\n- **Engagement Rates**: Monitoring appointment bookings, repeat visits, and digital interactions.\n- **Financial Metrics**: Revenue generation, cost efficiency, and long-term profitability.\n- **Operational Efficiency**: Time management during consultations and utilisation rates of physical spaces."
#     },
#     {
#       "Question": "How does the Centre address challenges from previous digital-only financial advisory approaches?",
#       "Answer": "The Centre mitigates previous challenges by:\n- **Integrating Personal Touch**: Offering face-to-face consultations that digital platforms miss.\n- **Structured Appointments**: Avoiding the pitfalls of rushed or impersonal digital interactions through scheduled consultations.\n- **Enhanced Communication**: Use of sensory cues (lighting, music, fragrance) to create a nurturing atmosphere that improves client comfort and engagement."
#     },
#     {
#       "Question": "What contingency plans are in place for unexpected operational challenges?",
#       "Answer": "Contingency planning is robust and includes:\n- **Backup Systems**: Redundant digital systems to manage appointments and data in case of technical glitches.\n- **Crisis Management**: Pre-established protocols, training for staff to handle unexpected situations.\n- **Flexible Resource Allocation**: Ability to adjust staffing and space usage immediately based on demand fluctuations."
#     },
#     {
#       "Question": "How will feedback from internal teams and clients shape future updates?",
#       "Answer": "Feedback is integral to our continuous improvement process. It is collected through:\n- **Regular Surveys**: Both digital and in-person feedback forms after consultations.\n- **Focus Groups**: Periodic meetings with client representatives and staff to review services.\n- **Iterative Updates**: Agile methodologies allow rapid adjustments in both technological and operational aspects."
#     },
#     {
#       "Question": "How will the roadmap for future expansion be structured?",
#       "Answer": "Future expansion focuses on:\n- **Digital Enhancements**: Upgrading the online interface and integrating AI-based advisory tools.\n- **Physical Upgrades**: Expanding consultation spaces based on demand and client feedback.\n- **Service Diversification**: Introducing additional advisory services such as wealth management and estate planning.\n- **Timeline Milestones**: Regular assessment phases to determine readiness for scaling operations."       
#     },
#     {
#       "Question": "What internal training programmes are in place to ensure staff readiness?",
#       "Answer": "Staff training is thorough and ongoing, encompassing:\n- **Technical Training**: Workshops on the latest software and digital tools.\n- **Client Engagement Workshops**: Role-playing and scenario training to build empathy and effective communication.\n- **Compliance and Legal Briefings**: Regular sessions to update staff on regulatory changes and privacy requirements."
#     },
#     {
#       "Question": "What communication strategies are used internally to coordinate across teams?",
#       "Answer": "Effective internal communication is maintained through:\n- **Regular Meetings**: Cross-departmental briefings to ensure all teams are aligned.\n- **Digital Dashboards**: Live updates on appointments, feedback, and performance metrics accessible to all stakeholders.\n- **Internal Newsletters**: Frequent updates on progress, challenges, and successes to encourage a collaborative environment."
#     },
#     {
#       "Question": "How is risk management integrated throughout the project lifecycle?",
#       "Answer": "Risk management is a continual process incorporating:\n- **Risk Assessment Frameworks**: Regular evaluations of potential operational, technical, and market risks.\n- **Mitigation Strategies**: Detailed action plans for each identified risk scenario, including response teams and backup resources.\n- **Performance Reviews**: Periodic audits and performance reviews to assess the effectiveness of risk management protocols."
#     }
#   ],
#   "ExternalFAQs": [
#     {
#       "Question": "What exactly is the Financial Planning Centre, and what services does it offer?",
#       "Answer": "The Financial Planning Centre is a dedicated advisory space that combines personalised consultations with sensory enhancements to deliver a uniquely engaging and supportive financial planning experience. Services include:\n- **One-on-One Consultations**: Personalised meetings with Qualified Financial Advisors (QFAs).\n- **Group Sessions**: Mini workshops and collective learning environments.\n- **Online and In-Person Integration**: Seamless digital booking with in-person execution that guarantees a bespoke advisory experience."
#     },
#     {
#       "Question": "How does the Financial Planning Centre address clients’ need for personalised financial advice?",
#       "Answer": "The Centre is designed to move away from a generic, digital-only approach by:\n- **Tailored Consultations**: Each session is customised based on the client's financial history and goals.\n- **Sensory-Enhanced Environment**: The ambiance (through music, lighting, and fragrances) creates a calming atmosphere that fosters open communication.\n- **Holistic Approach**: Integrating both digital tools and human expertise to ensure well-rounded advice."  
#     },
#     {
#       "Question": "Who is the ideal client for the Financial Planning Centre, and how can they benefit?",
#       "Answer": "The ideal client is typically an individual from a Tier I or Tier II city with a higher income (annual income above 10L+), seeking more personalised, hands-on financial advice. Benefits include:\n- **Personalised Service**: In-depth analysis and tailor-made financial strategies.\n- **Trust and Confidence**: Higher quality engagements owing to face-to-face interactions.\n- **Flexible Consultation Models**: Options available for both individual and group advisory sessions."
#     },
#     {
#       "Question": "What sets the Financial Planning Centre apart from digital-only advisory services?",
#       "Answer": "The Centre distinguishes itself by offering a blend of technology and personal interaction, including:\n- **In-Person Consultations**: Enhanced trust through direct interaction with financial experts.\n- **Sensory Experience**: Thoughtful design elements such as ambient lighting, soothing music, and subtle fragrances create a homely atmosphere.\n- **On-Demand Booking**: Structured appointment systems ensure quality, unhurried consultations."      
#     },
#     {
#       "Question": "How do I register or book a consultation at the Financial Planning Centre?",
#       "Answer": "Booking a consultation is designed to be user-friendly. The steps include:\n- **Online Registration**: Sign up via the website or mobile app.\n- **Appointment Selection**: Choose an available time slot with a Qualified Financial Advisor.\n- **Confirmation**: Receive a confirmation email with details and any pre-consultation forms.\n- **In-Person Visit**: Arrive at the centre at the scheduled time for a personalised consultation."
#     },
#     {
#       "Question": "What consultation settings are offered at the Centre?",
#       "Answer": "The Centre offers multiple settings to cater to diverse requirements:\n- **Private Meeting Rooms**: For one-on-one consultations, ensuring confidentiality.\n- **Group Spaces**: Designed for mini-workshops or collective learning sessions.\n- **Pods**: For remote consultations and as quiet workspaces for advisors.\n- **Versatile Configurations**: Each space is designed to maximise comfort and interaction."
#     },
#     {
#       "Question": "Could you detail the sensory experiences integrated within the Centre?",
#       "Answer": "The Centre’s design goes beyond conventional advisory services by incorporating sensory enhancements:\n- **Ambient Lighting**: Soft, reassuring lighting that promotes relaxation.\n- **Calming Music**: Background music tailored to reduce stress and foster focus.\n- **Aromatic Scents**: Subtle fragrances that create a welcoming atmosphere.\n- **Thoughtful Design**: A layout that reduces the formal 'office' feel in favour of a comforting, homely environment."
#     },
#     {
#       "Question": "What are the operating hours and location details of the Centre?",
#       "Answer": "The Centre operates daily from 9 am to 9 pm, offering flexibility for busy clients. It is located at:\n- **Address**: UNIT No. 1 to 5, ONE HIRANANDANI PARK, PATLIPADA, GHODBUNDER ROAD, THANE WEST - 400 607.\n- **Accessibility**: Situated in a high-income residential and corporate area to maximise convenience for its target demographic."
#     },
#     {
#       "Question": "How are appointments structured to ensure an unhurried, personalised experience?",
#       "Answer": "Appointments are carefully scheduled similar to a doctor's appointment system to ensure:\n- **Dedicated Time Slots**: Fixed times for each consultation, avoiding overlaps.\n- **Thorough Engagement**: Sufficient time allocated for discussions and follow-up questions.\n- **Efficient Service**: Pre-consultation processes that help tailor the session specifically to your financial needs."
#     },
#     {
#       "Question": "What pricing strategy has been adopted for services at the Centre?",
#       "Answer": "Pricing is reflective of the premium, personalised service offered and may vary based on consultation type. Key aspects include:\n- **Transparent Costs**: Detailed fee breakdowns provided at the time of booking.\n- **Value for Money**: Investment in a holistic financial planning experience that combines expert advice with a nurturing physical environment.\n- **Customised Packages**: Options available based on individual requirements and service frequency."
#     },
#     {
#       "Question": "Are there any known limitations or areas for improvement in the current service model?",
#       "Answer": "While the Centre delivers a uniquely personal approach, some considerations include:\n- **Limited Physical Capacity**: The in-person model is designed for high-touch interactions, meaning availability might be limited during peak times.\n- **Service Expansion**: Currently focused on personal finance advisory, with future plans to expand into areas like wealth and estate management.\n- **Adaption Period**: New clients may experience a brief adjustment period to get fully accustomed to the booking and consultation process."
#     },
#     {
#       "Question": "How secure is my personal data when I access the Centre’s services?",
#       "Answer": "Data security is a top priority and is ensured through:\n- **Industry-Standard Encryption**: Protecting data during storage and transmission.\n- **Strict Access Controls**: Only authorised personnel have access to sensitive information.\n- **Regular Security Audits**: Continuous monitoring and updates to safeguard client data."
#     },
#     {
#       "Question": "How is client privacy maintained during consultations?",
#       "Answer": "Privacy is ensured by:\n- **Discrete Consultation Rooms**: Designed for confidential, one-on-one discussions.\n- **Secure Digital Platforms**: Used to manage bookings and client records.\n- **Compliance with Data Protection Regulations**: Adhering to the highest standards in financial services."
#     },
#     {
#       "Question": "What regulatory compliances does the Financial Planning Centre adhere to?",
#       "Answer": "The Centre meets all industry standards and regulatory requirements, including:\n- **Financial Advising Regulations**: Ensuring transparent practices and ethical standards.\n- **Data Protection Laws**: Comprehensive compliance with data privacy and security regulations.\n- **Ongoing Audits**: Regular assessments to maintain compliance across all operations."
#     },
#     {
#       "Question": "Can I switch between online and in-person consultations seamlessly?",
#       "Answer": "Yes, the Centre’s omnichannel model is designed for ease:\n- **Integrated Booking System**: Allows switching between modes with minimal hassle.\n- **Unified Client Profile**: Your preferences and history are maintained across both platforms.\n- **Consistent Quality**: Whether online or in-person, the service quality remains uniform and tailored to your needs."
#     },
#     {
#       "Question": "What support options are available if I have further queries after my consultation?",
#       "Answer": "Support extends beyond the consultation itself, including:\n- **Follow-Up Calls/Emails**: Proactive follow-ups to address any lingering questions.\n- **Dedicated Customer Service**: Teams available via phone, email, or through our app to resolve issues.\n- **Feedback Channels**: Multiple avenues for submitting queries or suggestions to improve service quality."
#     },
#     {
#       "Question": "Are there integration features with other financial management tools?",
#       "Answer": "Integration is a key feature, achieved by:\n- **API Connectivity**: Capable of linking with popular financial planning and accounting software.\n- **Data Synchronisation**: Ensuring your financial data is consistent across all platforms.\n- **Customisable Solutions**: Catering to individual needs by supporting various integration protocols."
#     },
#     {
#       "Question": "What future updates or new features can clients expect?",
#       "Answer": "The Centre is committed to continuous innovation. Future enhancements include:\n- **Enhanced Digital Tools**: Incorporation of AI-driven insights into financial planning.\n- **Expanded Advisory Services**: Broadening the range to include wealth management, retirement planning, and more.\n- **Client Feedback Integration**: Regular updates based on client suggestions and industry advancements.\n- **Improved User Interface**: Further streamlining the booking and consultation processes."
#     },
#     {
#       "Question": "How does the Centre manage high-demand periods during peak hours?",
#       "Answer": "To handle increased demand:\n- **Dynamic Scheduling**: Adjustments to appointment slots to avoid overcrowding.\n- **Staggered Staffing**: Ensuring enough Qualified Financial Advisors are available during busy periods.\n- **Real-Time Updates**: Digital support systems that inform clients of the best available slots, ensuring minimal wait times."
#     },
#     {
#       "Question": "Can I consult with multiple advisors if I require different perspectives?",
#       "Answer": "Absolutely. The Centre supports a multi-disciplinary approach by:\n- **Flexible Consultations**: Scheduling back-to-back meetings with different experts as needed.\n- **Collaborative Sessions**: In select cases, joint appointments can be arranged for comprehensive advice.\n- **Expertise Matching**: Our system helps match your specific needs with the right advisor profiles, ensuring you have access to varied perspectives."
#     }
#   ]
# }
# """
# faq = json.dumps(curr_faq)

# from main import modify_faq

# resp = modify_faq(
#     existing_faq=faq,
#     user_feedback="give a table comparing the costs and subcosts of opening such centers in India in different cities, give appropriate numbers",
#     problem="Many clients have expressed concerns over the impersonal nature of online financial advisory, where building authentic trust can be challenging. The shi  to digital meetings has le  a gap for individuals who desire a face-to-face connection, leading to uncertainty and hesitance when seeking personalized financial advice.",
#     solution="The introduction of Financial Planning Centers addresses these issues by offering dedicated spaces for in-person consultations, ensuring clearer communication and stronger client relationships. This initiative, launched in the top cities across the region, particularly targets those seeking reliable and tangible support for their financial planning needs, ultimately enhancing client confidence and satisfaction.",
# )

# print(resp)
