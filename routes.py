import os
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Job, Candidate, CandidateComment
from services.ai_service import analyze_resume
from services.file_processor import process_uploaded_file
from sqlalchemy.exc import SQLAlchemyError
# Import will be done locally to avoid circular imports
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
    candidate_ids = []
    
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
            candidate_ids.append(candidate.id)
    
    # Start parallel AI analysis for all uploaded candidates
    if candidate_ids:
        logging.info(f"Starting parallel analysis for {len(candidate_ids)} candidates")
        from processors.background_processor import start_background_analysis
        start_background_analysis(candidate_ids)
        flash(f'{len(candidate_ids)} currículos enviados! A IA vai analisar TODOS os candidatos em paralelo (pode demorar alguns minutos).', 'success')
    else:
        flash('Nenhum arquivo válido foi enviado.', 'warning')
    
    return redirect(url_for('job_detail', job_id=job_id))

@app.route('/jobs/<int:job_id>/bulk-upload')
@login_required
def bulk_upload_page(job_id):
    """Page for bulk resume upload"""
    job = Job.query.get_or_404(job_id)
    return render_template('jobs/bulk_upload.html', job=job)

@app.route('/jobs/<int:job_id>/bulk-upload', methods=['POST'])
@login_required
def bulk_upload_process(job_id):
    """Process bulk resume upload with optimized batch processing"""
    try:
        job = Job.query.get_or_404(job_id)
        
        if 'files' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        files = request.files.getlist('files')
        if not files or all(not f.filename for f in files):
            return jsonify({'error': 'Nenhum arquivo válido enviado'}), 400
        
        logging.info(f"Starting optimized bulk upload for {len(files)} files")
        
        # Use simple immediate response to avoid timeout
        candidate_ids = []
        processed_count = 0
        errors = []
        
        for file in files:
            try:
                if not file.filename or file.filename == '':
                    continue
                
                # Quick processing - just save files
                filename = secure_filename(file.filename)
                if not filename:
                    filename = f"resume_{int(time.time())}.pdf"
                
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if file_ext not in ['pdf', 'docx', 'txt']:
                    continue
                
                # Save file
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Create candidate with minimal processing
                candidate = Candidate(
                    name=filename.rsplit('.', 1)[0],
                    filename=filename,
                    file_path=file_path,
                    file_type=file_ext,
                    job_id=job_id,
                    status='pending',
                    analysis_status='pending'
                )
                
                db.session.add(candidate)
                db.session.flush()
                candidate_ids.append(candidate.id)
                processed_count += 1
                
            except Exception as e:
                errors.append(f'Erro: {file.filename}')
        
        # Commit all at once
        db.session.commit()
        
        # Start simple background processing
        if candidate_ids:
            from simple_processor import start_simple_background_processing
            start_simple_background_processing(candidate_ids)
        
        result = {
            'processed_count': processed_count,
            'candidate_ids': candidate_ids,
            'errors': errors,
            'total_files': len(files)
        }
        
        return jsonify({
            'success': True,
            'processed_count': result['processed_count'],
            'candidate_ids': result['candidate_ids'],
            'errors': result['errors'],
            'total_files': result['total_files'],
            'message': f'{result["processed_count"]} currículos processados com sucesso! A IA está analisando todos em paralelo.'
        })
        
    except Exception as e:
        logging.error(f"Error in bulk upload: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no processamento: {str(e)}',
            'processed_count': 0,
            'candidate_ids': [],
            'errors': [str(e)]
        }), 500
    
    for file in files:
        if file and file.filename:
            try:
                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower()
                
                if file_ext not in ['pdf', 'docx', 'txt']:
                    errors.append(f'Formato não suportado: {filename}')
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
                
                try:
                    db.session.add(candidate)
                    db.session.flush()  # Flush to get ID without committing
                    candidate_id = candidate.id
                    db.session.commit()
                    candidate_ids.append(candidate_id)
                    processed_count += 1
                    logging.info(f"Successfully saved candidate: {filename} with ID: {candidate_id}")
                except SQLAlchemyError as db_error:
                    logging.error(f"Database error for {filename}: {db_error}")
                    db.session.rollback()
                    errors.append(f'Erro de banco para {filename}: {str(db_error)}')
                    continue
                except Exception as e:
                    logging.error(f"Unexpected error for {filename}: {e}")
                    db.session.rollback()
                    errors.append(f'Erro inesperado para {filename}: {str(e)}')
                    continue
            except Exception as e:
                logging.error(f"Error processing file {file.filename}: {e}")
                errors.append(f'Erro ao processar {file.filename}: {str(e)}')
    
    # Start parallel AI analysis for all uploaded candidates
    try:
        if candidate_ids:
            logging.info(f"Starting parallel analysis for {len(candidate_ids)} candidates")
            from parallel_processor import start_parallel_analysis
            start_parallel_analysis(candidate_ids)
        
        return jsonify({
            'success': True,
            'processed_count': processed_count,
            'candidate_ids': candidate_ids,
            'errors': errors,
            'message': f'{processed_count} currículos processados. A IA vai analisar TODOS os candidatos (pode demorar alguns minutos).'
        })
    except Exception as e:
        logging.error(f"Error in bulk upload response: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro no processamento: {str(e)}',
            'processed_count': processed_count,
            'candidate_ids': candidate_ids,
            'errors': errors
        }), 500

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
    
    if new_status in ['pending', 'interested', 'rejected']:
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

@app.route('/candidates/<int:candidate_id>/delete', methods=['POST'])
@login_required
def delete_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    job_id = candidate.job_id
    
    # Delete the physical file if it exists
    try:
        if os.path.exists(candidate.file_path):
            os.remove(candidate.file_path)
    except Exception as e:
        logging.warning(f"Could not delete file {candidate.file_path}: {e}")
    
    # Delete candidate from database
    candidate_name = candidate.name
    db.session.delete(candidate)
    db.session.commit()
    
    flash(f'Candidato "{candidate_name}" excluído com sucesso!', 'success')
    return redirect(url_for('job_detail', job_id=job_id))

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

@app.route('/api/jobs/<int:job_id>/processing_status')
def api_job_processing_status(job_id):
    """Get processing status for all candidates in a job"""
    try:
        job = Job.query.get_or_404(job_id)
        candidates = Candidate.query.filter_by(job_id=job_id).all()
        
        status_counts = {
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0,
            'total': len(candidates)
        }
        
        candidate_details = []
        
        for candidate in candidates:
            status_counts[candidate.analysis_status] += 1
            candidate_details.append({
                'id': candidate.id,
                'name': candidate.name,
                'analysis_status': candidate.analysis_status,
                'ai_score': candidate.ai_score,
                'analyzed_at': candidate.analyzed_at.isoformat() if candidate.analyzed_at else None
            })
        
        return jsonify({
            'status_counts': status_counts,
            'candidates': candidate_details,
            'progress_percentage': round((status_counts['completed'] + status_counts['failed']) / max(status_counts['total'], 1) * 100, 1)
        })
        
    except Exception as e:
        logging.error(f"Error getting processing status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/candidates/<int:candidate_id>/reprocess', methods=['POST'])
@login_required
def api_reprocess_candidate(candidate_id):
    """Reprocess a failed candidate"""
    try:
        candidate = Candidate.query.get_or_404(candidate_id)
        
        # Reset candidate status
        candidate.analysis_status = 'pending'
        candidate.ai_score = None
        candidate.ai_summary = None
        candidate.ai_analysis = None
        candidate.analyzed_at = None
        db.session.commit()
        
        # Start background processing
        from processors.background_processor import start_background_analysis
        start_background_analysis([candidate_id])
        
        return jsonify({
            'success': True,
            'message': f'Candidato {candidate.name} foi colocado na fila para reprocessamento'
        })
        
    except Exception as e:
        logging.error(f"Error reprocessing candidate {candidate_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/process-pending')
@login_required
def api_process_pending():
    """Manually trigger processing of pending candidates"""
    try:
        pending_candidates = Candidate.query.filter_by(analysis_status='pending').all()
        if not pending_candidates:
            return jsonify({'success': False, 'message': 'Nenhum candidato pendente encontrado'})
        
        candidate_ids = [c.id for c in pending_candidates]
        
        from processors.background_processor import start_background_analysis
        start_background_analysis(candidate_ids)
        
        return jsonify({
            'success': True, 
            'message': f'Processamento iniciado para {len(candidate_ids)} candidatos',
            'candidate_ids': candidate_ids
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

from datetime import datetime

@app.route('/jobs/<int:job_id>/processing-monitor')
@login_required
def processing_monitor(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('jobs/processing_monitor.html', job=job)
