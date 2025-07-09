import os
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Job, Candidate, CandidateComment
from ai_service import analyze_resume
from file_processor import process_uploaded_file
import logging

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'recruiter')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email já está em uso.', 'error')
            return render_template('auth/register.html')
        
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Main routes
@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/site-info')
def site_info():
    """Show direct URL for opening in new tab"""
    return """
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
        <h2>🌐 Viana e Moura - Acesso Direto</h2>
        <p>Para abrir o site em uma nova aba, use o URL direto:</p>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <strong>URL: </strong><span id="direct-url">Carregando...</span>
        </div>
        <p><a href="/login" style="color: #B93A3E; text-decoration: none;">← Voltar para Login</a></p>
        
        <script>
            const url = window.location.protocol + '//' + window.location.host;
            document.getElementById('direct-url').innerHTML = 
                '<a href="' + url + '" target="_blank" style="color: #B93A3E;">' + url + '</a>';
        </script>
    </div>
    """

@app.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    total_jobs = Job.query.count()
    total_candidates = Candidate.query.count()
    analyzed_candidates = Candidate.query.filter_by(analysis_status='completed').count()
    
    # Get recent jobs
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()
    
    # Get top candidates (by score)
    top_candidates = Candidate.query.filter(
        Candidate.ai_score.isnot(None)
    ).order_by(Candidate.ai_score.desc()).limit(10).all()
    
    # Get score distribution for chart
    score_ranges = {
        '0-2': 0, '2-4': 0, '4-6': 0, '6-8': 0, '8-10': 0
    }
    
    candidates_with_scores = Candidate.query.filter(Candidate.ai_score.isnot(None)).all()
    for candidate in candidates_with_scores:
        score = candidate.ai_score
        if score <= 2:
            score_ranges['0-2'] += 1
        elif score <= 4:
            score_ranges['2-4'] += 1
        elif score <= 6:
            score_ranges['4-6'] += 1
        elif score <= 8:
            score_ranges['6-8'] += 1
        else:
            score_ranges['8-10'] += 1
    
    return render_template('dashboard.html',
                         total_jobs=total_jobs,
                         total_candidates=total_candidates,
                         analyzed_candidates=analyzed_candidates,
                         recent_jobs=recent_jobs,
                         top_candidates=top_candidates,
                         score_ranges=score_ranges)

# Job management routes
@app.route('/jobs')
@login_required
def jobs_list():
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return render_template('jobs/list.html', jobs=jobs)

@app.route('/jobs/create', methods=['GET', 'POST'])
@login_required
def create_job():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        requirements = request.form['requirements']
        dcf_content = request.form.get('dcf_content', '')
        
        job = Job(
            title=title,
            description=description,
            requirements=requirements,
            dcf_content=dcf_content,
            created_by=current_user.id
        )
        
        db.session.add(job)
        db.session.commit()
        
        flash('Vaga criada com sucesso!', 'success')
        return redirect(url_for('job_detail', job_id=job.id))
    
    return render_template('jobs/create.html')

@app.route('/jobs/<int:job_id>')
@login_required
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    candidates = Candidate.query.filter_by(job_id=job_id).order_by(
        Candidate.ai_score.desc().nullslast()
    ).all()
    
    # Get filter parameters
    min_score = request.args.get('min_score', type=float)
    status_filter = request.args.get('status')
    
    # Apply filters
    if min_score is not None:
        candidates = [c for c in candidates if c.ai_score and c.ai_score >= min_score]
    
    if status_filter:
        candidates = [c for c in candidates if c.status == status_filter]
    
    return render_template('jobs/detail.html', job=job, candidates=candidates)

@app.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    if request.method == 'POST':
        job.title = request.form['title']
        job.description = request.form['description']
        job.requirements = request.form['requirements']
        job.dcf_content = request.form.get('dcf_content', '')
        
        db.session.commit()
        flash('Vaga atualizada com sucesso!', 'success')
        return redirect(url_for('job_detail', job_id=job.id))
    
    return render_template('jobs/create.html', job=job)

@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    if not current_user.is_admin():
        flash('Permissão negada.', 'error')
        return redirect(url_for('jobs_list'))
    
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    
    flash('Vaga excluída com sucesso!', 'success')
    return redirect(url_for('jobs_list'))

# Resume upload and processing
@app.route('/jobs/<int:job_id>/upload', methods=['POST'])
@login_required
def upload_resume(job_id):
    job = Job.query.get_or_404(job_id)
    
    if 'resumes' not in request.files:
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(url_for('job_detail', job_id=job_id))
    
    files = request.files.getlist('resumes')
    
    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            
            if file_ext not in ['pdf', 'docx', 'txt']:
                flash(f'Formato não suportado: {filename}', 'error')
                continue
            
            # Save file
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process file to extract basic info
            try:
                name, email, phone = process_uploaded_file(file_path, file_ext)
            except Exception as e:
                logging.error(f"Error processing file {filename}: {e}")
                name = filename.rsplit('.', 1)[0]
                email = None
                phone = None
            
            # Create candidate record
            candidate = Candidate(
                name=name,
                email=email,
                phone=phone,
                filename=filename,
                file_path=file_path,
                file_type=file_ext,
                job_id=job_id,
                status='pending',
                analysis_status='pending'
            )
            
            db.session.add(candidate)
            db.session.commit()
            
            # Start AI analysis in background (simplified for demo)
            try:
                candidate.analysis_status = 'processing'
                db.session.commit()
                
                # Analyze resume
                analysis_result = analyze_resume(file_path, file_ext, job)
                
                # Update candidate with results
                candidate.ai_score = analysis_result['score']
                candidate.ai_summary = analysis_result['summary']
                candidate.ai_analysis = analysis_result['analysis']
                candidate.set_skills_list(analysis_result['skills'])
                candidate.analysis_status = 'completed'
                candidate.analyzed_at = datetime.utcnow()
                
                db.session.commit()
                
            except Exception as e:
                logging.error(f"Error analyzing resume {filename}: {e}")
                candidate.analysis_status = 'failed'
                db.session.commit()
    
    flash('Currículos enviados com sucesso!', 'success')
    return redirect(url_for('job_detail', job_id=job_id))

# Candidate management
@app.route('/candidates')
@login_required
def candidates_list():
    candidates = Candidate.query.order_by(Candidate.ai_score.desc().nullslast()).all()
    return render_template('candidates/list.html', candidates=candidates)

@app.route('/candidates/<int:candidate_id>')
@login_required
def candidate_detail(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    comments = CandidateComment.query.filter_by(candidate_id=candidate_id).order_by(
        CandidateComment.created_at.desc()
    ).all()
    return render_template('candidates/detail.html', candidate=candidate, comments=comments)

@app.route('/candidates/<int:candidate_id>/update_status', methods=['POST'])
@login_required
def update_candidate_status(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    new_status = request.form['status']
    
    if new_status in ['pending', 'interested', 'rejected', 'interview']:
        candidate.status = new_status
        db.session.commit()
        flash('Status atualizado com sucesso!', 'success')
    else:
        flash('Status inválido.', 'error')
    
    return redirect(url_for('candidate_detail', candidate_id=candidate_id))

@app.route('/candidates/<int:candidate_id>/comment', methods=['POST'])
@login_required
def add_comment(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    content = request.form['content']
    
    comment = CandidateComment(
        content=content,
        candidate_id=candidate_id,
        user_id=current_user.id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    flash('Comentário adicionado com sucesso!', 'success')
    return redirect(url_for('candidate_detail', candidate_id=candidate_id))

# API endpoints for real-time updates
@app.route('/api/candidate/<int:candidate_id>/status')
@login_required
def api_candidate_status(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    return jsonify({
        'id': candidate.id,
        'analysis_status': candidate.analysis_status,
        'ai_score': candidate.ai_score,
        'status': candidate.status
    })

from datetime import datetime
