import streamlit as st
import hashlib
import time
import os
from datetime import datetime, timedelta
from io import BytesIO
try:
    from streamlit_option_menu import option_menu
except ImportError:
    st.error("The 'streamlit-option-menu' package is not installed. Please install it using 'pip install streamlit-option-menu'")
    st.stop()
import io
import re

# Configuração da página
st.set_page_config(layout="wide", page_title="Justificações Acadêmicas", page_icon="🎓")

# Função para extrair ID do vídeo do YouTube
def extract_youtube_id(url):
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# Função para extrair ID do arquivo do Google Drive
def extract_drive_id(url):
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# Função atualizada para gerar URL de download do Google Drive
def get_drive_download_link(file_id):
    return f"https://drive.google.com/file/d/{file_id}/view"

# Inicialização do estado da sessão
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.course_files = {}
    
    # Exemplo de vídeo pré-carregado do YouTube
    youtube_example = "https://youtu.be/DN5RpUAmyYM"
    file_key = "curso1_lesson_1_video"
    st.session_state.course_files[file_key] = {
        'content': extract_youtube_id(youtube_example),
        'type': 'youtube'
    }
    
    # Exemplo de PDF pré-carregado do Google Drive
    drive_example = "https://drive.google.com/file/d/seu_id_aqui/view"
    pdf_key = "curso1_lesson_1_pdf"
    st.session_state.course_files[pdf_key] = {
        'content': extract_drive_id(drive_example),
        'type': 'google_drive'
    }
    
    # Inicializar banco de dados de usuários
    st.session_state.users_db = {
        'admin@email.com': {
            'password': hashlib.sha256('admin123'.encode()).hexdigest(),
            'permissions': ['admin'],
            'last_login': None,
            'session_id': None
        },
        'estudante@email.com': {
            'password': hashlib.sha256('senha123'.encode()).hexdigest(),
            'permissions': ['curso1'],
            'progress': {'curso1': 1},
            'last_login': None,
            'session_id': None
        }
    }
    
    # Inicializar banco de dados de cursos
    st.session_state.courses_db = {
        'curso1': {
            'name': 'Curso 1',
            'topics': "Tópicos do Curso 1",
            'lessons': {
                1: {
                    'video': {'file_key': "curso1_lesson_1_video"},
                    'pdf': {'file_key': "curso1_lesson_1_pdf"}
                }
            },
            'quizzes': {
                1: [
                    {"question": "Qual é a primeira pergunta?", "answer": "resposta1"},
                    {"question": "Qual é a segunda pergunta?", "answer": "resposta2"},
                    {"question": "Qual é a terceira pergunta?", "answer": "resposta3"},
                    {"question": "Qual é a quarta pergunta?", "answer": "resposta4"},
                    {"question": "Qual é a quinta pergunta?", "answer": "resposta5"}
                ]
            },
            'feedback': []
        }
    }
    
    # Adicionar outros cursos
    for i in range(2, 11):
        st.session_state.courses_db[f'curso{i}'] = {
            'name': f'Curso {i}',
            'topics': "",
            'lessons': {},
            'quizzes': {},
            'feedback': []
        }

# Estilização
st.markdown("""
    <style>
    .big-font {
        font-size:35px !important;
        font-weight: bold;
        text-align: center;
        margin-bottom: 30px;
        color: #1E3D59;
    }
    .medium-font {
        font-size:20px !important;
    }
    .stButton>button {
        color: #4F8BF9;
        border-radius: 50px;
        height: 3em;
        width: 100%;
    }
    .iframe-container {
        position: relative;
        width: 100%;
        padding-bottom: 56.25%;
        height: 0;
        margin-bottom: 20px;
    }
    .iframe-container iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }
    .download-button {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 8px 16px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        width: auto;
        max-width: 200px;
    }
    .download-button:hover {
        background-color: #45a049;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: translateY(-1px);
    }
    .quiz-container {
        margin-top: 2rem;
        padding: 1rem;
        border-radius: 10px;
        background-color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

def save_uploaded_file(uploaded_file, course, lesson_number, file_type, video_url=None, pdf_url=None):
    file_key = f"{course}_lesson_{lesson_number}_{file_type}"
    try:
        if file_type == 'video' and video_url:
            video_id = extract_youtube_id(video_url)
            if video_id:
                st.session_state.course_files[file_key] = {
                    'content': video_id,
                    'type': 'youtube'
                }
                if 'lessons' not in st.session_state.courses_db[course]:
                    st.session_state.courses_db[course]['lessons'] = {}
                if lesson_number not in st.session_state.courses_db[course]['lessons']:
                    st.session_state.courses_db[course]['lessons'][lesson_number] = {}
                st.session_state.courses_db[course]['lessons'][lesson_number]['video'] = {'file_key': file_key}
            else:
                st.error("URL do YouTube inválida")
                return False
        elif file_type == 'pdf' and pdf_url:
            drive_id = extract_drive_id(pdf_url)
            if drive_id:
                st.session_state.course_files[file_key] = {
                    'content': drive_id,
                    'type': 'google_drive',
                    'url': pdf_url
                }
                if 'lessons' not in st.session_state.courses_db[course]:
                    st.session_state.courses_db[course]['lessons'] = {}
                if lesson_number not in st.session_state.courses_db[course]['lessons']:
                    st.session_state.courses_db[course]['lessons'][lesson_number] = {}
                st.session_state.courses_db[course]['lessons'][lesson_number]['pdf'] = {'file_key': file_key}
            else:
                st.error("URL do Google Drive inválida")
                return False
        return True
    except Exception as e:
        st.error(f"Erro ao salvar arquivo: {str(e)}")
        return False

def get_file_content(file_key):
    if file_key in st.session_state.course_files:
        return st.session_state.course_files[file_key]
    return None

def check_password(email, password):
    if email in st.session_state.users_db:
        return st.session_state.users_db[email]['password'] == hashlib.sha256(password.encode()).hexdigest()
    return False

def get_user_permissions(email):
    return st.session_state.users_db[email]['permissions']

def login(email, password):
    if check_password(email, password):
        user = st.session_state.users_db[email]
        current_time = datetime.now()
        if user['session_id'] and user['last_login']:
            last_login = datetime.fromisoformat(user['last_login'])
            if current_time - last_login < timedelta(hours=1):
                st.error("Esta conta já está em uso em outra sessão.")
                return False
        session_id = hashlib.sha256(f"{email}{time.time()}".encode()).hexdigest()
        user['session_id'] = session_id
        user['last_login'] = current_time.isoformat()
        st.session_state.logged_in = True
        st.session_state.user_email = email
        st.session_state.session_id = session_id
        return True
    return False

def logout():
    if st.session_state.logged_in:
        user = st.session_state.users_db[st.session_state.user_email]
        user['session_id'] = None
        user['last_login'] = None
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.session_id = None

def save_quiz(course, lesson_number, questions):
    if course not in st.session_state.courses_db:
        st.session_state.courses_db[course] = {'quizzes': {}}
    st.session_state.courses_db[course]['quizzes'][lesson_number] = questions

def check_quiz_answers(course, lesson_number, user_answers):
    if course in st.session_state.courses_db and lesson_number in st.session_state.courses_db[course]['quizzes']:
        correct_answers = st.session_state.courses_db[course]['quizzes'][lesson_number]
        return [ua.lower().strip() == ca['answer'].lower().strip() for ua, ca in zip(user_answers, correct_answers)]
    return []

def main():
    st.markdown('<p class="big-font">Justificações Acadêmicas - Cursos Online</p>', unsafe_allow_html=True)
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        login_interface()
    else:
        logged_in_interface()

def login_interface():
    st.markdown('<p class="medium-font">Login</p>', unsafe_allow_html=True)
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input('📧 E-mail')
        with col2:
            password = st.text_input('🔒 Senha', type='password')
        submit_button = st.form_submit_button("🚀 Entrar")
        if submit_button:
            if login(email, password):
                st.success("Login bem-sucedido!")
                st.rerun()
            else:
                st.error('E-mail ou senha incorretos')

def logged_in_interface():
    st.sidebar.markdown(f'👤 Bem-vindo, {st.session_state.user_email}!')
    if 'admin' in get_user_permissions(st.session_state.user_email):
        admin_menu()
    else:
        student_menu()
    if st.sidebar.button('🚪 Logout'):
        logout()
        st.rerun()

def admin_menu():
    choice = option_menu(
        menu_title="Menu Administrativo",
        options=["Gerenciar Cursos", "Gerenciar Usuários", "Gerenciar Conteúdo"],
        icons=["book", "people", "file-earmark-text"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )
    if choice == "Gerenciar Cursos":
        manage_courses()
    elif choice == "Gerenciar Usuários":
        manage_users()
    elif choice == "Gerenciar Conteúdo":
        manage_content()

def student_menu():
    permissions = get_user_permissions(st.session_state.user_email)
    choice = option_menu(
        menu_title="Menu do Estudante",
        options=["Meus Cursos", "Progresso", "Ajuda", "Feedbacks"],
        icons=["book", "graph-up", "question-circle", "chat-dots"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )
    if choice == "Meus Cursos":
        show_student_courses(permissions)
    elif choice == "Progresso":
        show_student_progress(permissions)
    elif choice == "Ajuda":
        show_help()
    elif choice == "Feedbacks":
        show_all_feedbacks()

def show_all_feedbacks():
    st.markdown('<p class="medium-font">Feedbacks dos Cursos</p>', unsafe_allow_html=True)
    for course_id, course_data in st.session_state.courses_db.items():
        if course_data['feedback']:
            st.subheader(f"🎓 {course_data['name']}")
            for idx, feedback in enumerate(course_data['feedback'], 1):
                st.write(f"📝 Feedback {idx}: {feedback}")
            st.divider()

def manage_courses():
    st.markdown('<p class="medium-font">Gerenciar Cursos</p>', unsafe_allow_html=True)
    course = st.selectbox('🎓 Selecione um curso', list(st.session_state.courses_db.keys()))
    new_name = st.text_input("📝 Nome do curso", value=st.session_state.courses_db[course]['name'])
    if new_name != st.session_state.courses_db[course]['name']:
        st.session_state.courses_db[course]['name'] = new_name
        st.success(f"Nome do curso atualizado para: {new_name}")
    topics = st.text_area("📚 Tópicos do curso", value=st.session_state.courses_db[course]['topics'])
    if topics != st.session_state.courses_db[course]['topics']:
        st.session_state.courses_db[course]['topics'] = topics
        st.success("Tópicos do curso atualizados!")

def manage_users():
    st.markdown('<p class="medium-font">Gerenciar Usuários</p>', unsafe_allow_html=True)
    user_email = st.selectbox('👤 Selecione um usuário', [user for user in st.session_state.users_db if user != 'admin@email.com'])
    user_permissions = st.multiselect('🔐 Selecione os cursos que o usuário pode acessar', 
                                      list(st.session_state.courses_db.keys()), 
                                      default=st.session_state.users_db[user_email]['permissions'])
    if st.button('📝 Atualizar Permissões'):
        st.session_state.users_db[user_email]['permissions'] = user_permissions
        st.success(f"Permissões atualizadas para {user_email}")

def manage_content():
    st.markdown('<p class="medium-font">Gerenciar Conteúdo do Curso</p>', unsafe_allow_html=True)
    course = st.selectbox('🎓 Selecione um curso', list(st.session_state.courses_db.keys()))
    lesson_number = st.number_input('📚 Número da aula', min_value=1, max_value=20, value=1)
    
    st.subheader("📹 Vídeo da Aula")
    st.info("Cole o link completo do YouTube (ex: https://youtube.com/watch?v=XXXX ou https://youtu.be/XXXX)")
    video_url = st.text_input("Link do YouTube:")
    if video_url and st.button("Salvar Vídeo"):
        if save_uploaded_file(None, course, lesson_number, 'video', video_url=video_url):
            st.success("Vídeo adicionado com sucesso!")
    
    st.subheader("📄 PDF da Aula")
    st.info("Cole o link de compartilhamento do Google Drive (ex: https://drive.google.com/file/d/XXXX/view)")
    pdf_url = st.text_input("Link do Google Drive:")
    if pdf_url and st.button("Salvar PDF"):
        if save_uploaded_file(None, course, lesson_number, 'pdf', pdf_url=pdf_url):
            st.success("PDF adicionado com sucesso!")

    st.subheader("❓ Quiz da Aula")
    manage_quiz(course, lesson_number)

def manage_quiz(course, lesson_number):
    st.write("Criar/Editar Quiz")
    current_quiz = st.session_state.courses_db[course].get('quizzes', {}).get(lesson_number, [])
    if not current_quiz:
        current_quiz = [{"question": "", "answer": ""} for _ in range(5)]
    
    updated_questions = []
    for i in range(5):
        st.markdown(f"### Pergunta {i+1}")
        question = st.text_input(
            "Digite a pergunta:",
            value=current_quiz[i].get('question', '') if i < len(current_quiz) else '',
            key=f"q_{course}_{lesson_number}_{i}"
        )
        answer = st.text_input(
            "Digite a resposta:",
            value=current_quiz[i].get('answer', '') if i < len(current_quiz) else '',
            key=f"a_{course}_{lesson_number}_{i}"
        )
        if question and answer:
            updated_questions.append({"question": question, "answer": answer})
    
    if st.button("💾 Salvar Quiz", key=f"save_quiz_{course}_{lesson_number}"):
        if len(updated_questions) == 5:
            save_quiz(course, lesson_number, updated_questions)
            st.success("Quiz salvo com sucesso!")
        else:
            st.error("Por favor, preencha todas as perguntas e respostas.")

def show_student_courses(permissions):
    st.markdown('<p class="medium-font">Meus Cursos</p>', unsafe_allow_html=True)
    course_selection = st.selectbox('🎓 Selecione um curso', permissions)
    if course_selection:
        show_course_content(course_selection)

def show_course_content(course_selection):
    course = st.session_state.courses_db[course_selection]
    st.header(course['name'])
    st.write("📚 Tópicos do curso:")
    st.write(course['topics'])
    
    if 'progress' not in st.session_state.users_db[st.session_state.user_email]:
        st.session_state.users_db[st.session_state.user_email]['progress'] = {}
    if course_selection not in st.session_state.users_db[st.session_state.user_email]['progress']:
        st.session_state.users_db[st.session_state.user_email]['progress'][course_selection] = 1
        
    current_lesson = st.session_state.users_db[st.session_state.user_email]['progress'][course_selection]
    available_lessons = list(range(1, current_lesson + 1))
    selected_lesson = st.selectbox("📚 Selecione a aula", available_lessons, index=len(available_lessons)-1)
    
    if selected_lesson in course['lessons']:
        st.subheader(f"📚 Aula {selected_lesson}")
        lesson_content = course['lessons'][selected_lesson]
        
        # Exibir vídeo do YouTube
        if 'video' in lesson_content:
            video_data = get_file_content(lesson_content['video']['file_key'])
            if video_data and video_data['type'] == 'youtube':
                video_id = video_data['content']
                st.markdown(f"""
                    <div class="iframe-container">
                        <iframe 
                            src="https://www.youtube-nocookie.com/embed/{video_id}?rel=0&modestbranding=1"
                            frameborder="0"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowfullscreen>
                        </iframe>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("---")
        
        # Exibir botão de download do PDF
        if 'pdf' in lesson_content:
            pdf_data = get_file_content(lesson_content['pdf']['file_key'])
            if pdf_data and pdf_data['type'] == 'google_drive':
                drive_id = pdf_data['content']
                view_link = get_drive_download_link(drive_id)
                col1, col2, col3 = st.columns([2,1,2])
                with col2:
                    st.markdown(f"""
                        <a href="{view_link}" target="_blank" class="download-button">
                            📥 Ver Material
                        </a>
                        """, unsafe_allow_html=True)
                st.markdown("---")
        
        # Exibir Quiz
        if selected_lesson in course.get('quizzes', {}):
            st.markdown('<div class="quiz-container">', unsafe_allow_html=True)
            st.subheader("❓ Quiz da Aula")
            show_quiz(course_selection, selected_lesson)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("🎉 Todas as aulas disponíveis foram concluídas!")

def show_quiz(course_selection, current_lesson):
    quiz_data = st.session_state.courses_db[course_selection]['quizzes'][current_lesson]
    st.write("⚠️ Responda todas as perguntas corretamente para avançar para a próxima aula")
    
    with st.form(key=f"quiz_form_{course_selection}_{current_lesson}"):
        user_answers = []
        for i, q in enumerate(quiz_data):
            st.write(f"**Pergunta {i+1}:** {q['question']}")
            answer = st.text_input(
                "Sua resposta:",
                key=f"quiz_answer_{course_selection}_{current_lesson}_{i}"
            )
            user_answers.append(answer)
        
        submit_quiz = st.form_submit_button("📝 Enviar Respostas")
        
        if submit_quiz:
            if all(answer.strip() for answer in user_answers):
                results = check_quiz_answers(course_selection, current_lesson, user_answers)
                all_correct = all(results)
                
                for i, (is_correct, question) in enumerate(zip(results, quiz_data)):
                    if is_correct:
                        st.success(f"✅ Pergunta {i+1}: Correta!")
                    else:
                        st.error(f"❌ Pergunta {i+1}: Incorreta. A resposta correta é: {question['answer']}")
                
                if all_correct:
                    st.balloons()
                    st.success("🎉 Parabéns! Você completou o quiz com sucesso!")
                    
                    if current_lesson == st.session_state.users_db[st.session_state.user_email]['progress'][course_selection]:
                        st.session_state.users_db[st.session_state.user_email]['progress'][course_selection] += 1
                        st.info("📚 Próxima aula desbloqueada!")
                        st.rerun()  # Aqui está a correção
                else:
                    st.warning("⚠️ Tente novamente. Você precisa acertar todas as perguntas para avançar.")
            else:
                st.warning("⚠️ Por favor, responda todas as perguntas antes de enviar.")

def show_student_progress(permissions):
    st.markdown('<p class="medium-font">Meu Progresso</p>', unsafe_allow_html=True)
    for course in permissions:
        if course in st.session_state.courses_db:
            progress = st.session_state.users_db[st.session_state.user_email].get('progress', {})
            current_lesson = progress.get(course, 1)
            total_lessons = len(st.session_state.courses_db[course]['lessons'])
            if total_lessons > 0:
                progress_percentage = min((current_lesson - 1) / total_lessons, 1.0)
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"🎓 {st.session_state.courses_db[course]['name']}")
                    st.progress(progress_percentage)
                with col2:
                    st.write(f"Aula {current_lesson-1} de {total_lessons}")
            else:
                st.info(f"🎓 {st.session_state.courses_db[course]['name']}: Aguardando conteúdo")

def show_help():
    st.markdown('<p class="medium-font">Ajuda</p>', unsafe_allow_html=True)
    st.write("""
    ℹ️ Como usar o sistema de cursos online:
    
    1. **Aulas e Conteúdo**
        - Cada curso é composto por aulas sequenciais
        - As aulas incluem vídeos e documentos em PDF
        - O conteúdo é protegido e só pode ser acessado através desta plataforma
    
    2. **Sistema de Quiz**
        - Após cada aula, há um quiz com 5 perguntas
        - Você precisa acertar todas as perguntas para avançar
        - Pode tentar o quiz quantas vezes precisar
    
    3. **Progresso**
        - Seu progresso é salvo automaticamente
        - Pode acompanhar seu avanço na aba "Progresso"
        - Aulas anteriores ficam disponíveis para revisão
    
    4. **Feedback**
        - Ao concluir cada aula, você pode deixar seu feedback
        - Os feedbacks ajudam a melhorar o conteúdo
    
    5. **Suporte**
        - Em caso de problemas técnicos, contate o administrador
        - Se tiver dúvidas sobre o conteúdo, use o espaço de feedback
    
    🔐 Observação: Por questões de segurança, não é permitido
    compartilhar links diretos dos materiais do curso.
    """)

if __name__ == '__main__':
    main()