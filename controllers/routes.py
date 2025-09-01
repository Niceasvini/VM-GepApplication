import os
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models.models import User, Job, Candidate, CandidateComment
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
        
        # Try to find user by username first, then by email
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User.query.filter_by(email=username).first()
        
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



@app.route('/dashboard')
@login_required
def dashboard():
    # Get statistics for current user only (admin can see all)
    if current_user.is_admin():
        # Admin sees all data
        total_jobs = Job.query.count()
        total_candidates = Candidate.query.count()
        analyzed_candidates = Candidate.query.filter_by(analysis_status='completed').count()
        recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()
        candidates_with_scores = Candidate.query.filter(Candidate.ai_score.isnot(None)).all()
        top_candidates = Candidate.query.filter(
            Candidate.ai_score.isnot(None)
        ).order_by(Candidate.ai_score.desc()).limit(10).all()
    else:
        # Regular users see only their own data
        user_jobs = Job.query.filter_by(created_by=current_user.id)
        user_job_ids = [job.id for job in user_jobs]
        
        total_jobs = user_jobs.count()
        total_candidates = Candidate.query.filter(Candidate.job_id.in_(user_job_ids)).count()
        analyzed_candidates = Candidate.query.filter(
            Candidate.job_id.in_(user_job_ids),
            Candidate.analysis_status == 'completed'
        ).count()
        
        recent_jobs = user_jobs.order_by(Job.created_at.desc()).limit(5).all()
        candidates_with_scores = Candidate.query.filter(
            Candidate.job_id.in_(user_job_ids),
            Candidate.ai_score.isnot(None)
        ).all()
        top_candidates = Candidate.query.filter(
            Candidate.job_id.in_(user_job_ids),
            Candidate.ai_score.isnot(None)
        ).order_by(Candidate.ai_score.desc()).limit(10).all()
    
    # Get score distribution for chart
    score_ranges = {
        '0-2': 0, '2-4': 0, '4-6': 0, '6-8': 0, '8-10': 0
    }
    
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
    
    # Get candidate status distribution for pie chart
    if current_user.is_admin():
        # Admin sees all candidates
        status_counts = db.session.query(
            Candidate.status, 
            db.func.count(Candidate.id)
        ).group_by(Candidate.status).all()
    else:
        # Regular users see only their candidates
        status_counts = db.session.query(
            Candidate.status, 
            db.func.count(Candidate.id)
        ).filter(Candidate.job_id.in_(user_job_ids)).group_by(Candidate.status).all()
    
    # Convert to dictionary for template
    candidate_status = {}
    for status, count in status_counts:
        candidate_status[status] = count
    
    # Convert top_candidates to serializable dictionaries
    top_candidates_data = []
    for candidate in top_candidates:
        candidate_dict = {
            'id': candidate.id,
            'name': candidate.name,
            'email': candidate.email,
            'phone': candidate.phone,
            'ai_score': candidate.ai_score,
            'status': candidate.status,
            'analysis_status': candidate.analysis_status,
            'uploaded_at': candidate.uploaded_at.isoformat() if candidate.uploaded_at else None,
            'job': {
                'id': candidate.job.id,
                'title': candidate.job.title
            }
        }
        top_candidates_data.append(candidate_dict)
    
    return render_template('dashboard.html',
                         total_jobs=total_jobs,
                         total_candidates=total_candidates,
                         analyzed_candidates=analyzed_candidates,
                         recent_jobs=recent_jobs,
                         top_candidates=top_candidates_data,
                         score_ranges=score_ranges,
                         candidate_status=candidate_status)

# Job management routes
@app.route('/jobs')
@login_required
def jobs_list():
    # Users only see their own jobs, admin sees all
    if current_user.is_admin():
        jobs = Job.query.order_by(Job.created_at.desc()).all()
    else:
        jobs = Job.query.filter_by(created_by=current_user.id).order_by(Job.created_at.desc()).all()
    return render_template('jobs/list.html', jobs=jobs)

@app.route('/jobs/create', methods=['GET', 'POST'])
@login_required
def create_job():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        requirements = request.form['requirements']
        
        job = Job(
            title=title,
            description=description,
            requirements=requirements,
            created_by=current_user.id
        )
        
        db.session.add(job)
        db.session.commit()
        
        flash('Vaga criada com sucesso! Agora você pode fazer upload de currículos para análise.', 'success')
        return redirect(url_for('job_detail', job_id=job.id))
    
    return render_template('jobs/create.html')

@app.route('/jobs/<int:job_id>')
@login_required
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if user has access to this job
    if not current_user.is_admin() and job.created_by != current_user.id:
        flash('Acesso negado. Você só pode ver suas próprias vagas.', 'error')
        return redirect(url_for('jobs_list'))
    
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
    
    # Check if user has access to edit this job
    if not current_user.is_admin() and job.created_by != current_user.id:
        flash('Acesso negado. Você só pode editar suas próprias vagas.', 'error')
        return redirect(url_for('jobs_list'))
    
    if request.method == 'POST':
        job.title = request.form['title']
        job.description = request.form['description']
        job.requirements = request.form['requirements']
        
        db.session.commit()
        flash('Vaga atualizada com sucesso!', 'success')
        return redirect(url_for('job_detail', job_id=job.id))
    
    return render_template('jobs/create.html', job=job)

@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if user has access to delete this job
    if not current_user.is_admin() and job.created_by != current_user.id:
        flash('Acesso negado. Você só pode excluir suas próprias vagas.', 'error')
        return redirect(url_for('jobs_list'))
    
    db.session.delete(job)
    db.session.commit()
    
    flash('Vaga excluída com sucesso!', 'success')
    return redirect(url_for('jobs_list'))

# Resume upload and processing
@app.route('/jobs/<int:job_id>/upload', methods=['POST'])
@login_required
def upload_resume(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if user has access to upload to this job
    if not current_user.is_admin() and job.created_by != current_user.id:
        flash('Acesso negado. Você só pode fazer upload para suas próprias vagas.', 'error')
        return redirect(url_for('jobs_list'))
    
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
    
    # Check if user has access to this job
    if not current_user.is_admin() and job.created_by != current_user.id:
        flash('Acesso negado. Você só pode fazer upload para suas próprias vagas.', 'error')
        return redirect(url_for('jobs_list'))
    
    return render_template('jobs/bulk_upload.html', job=job)

@app.route('/jobs/<int:job_id>/bulk-upload', methods=['POST'])
@login_required
def bulk_upload_process(job_id):
    """Process bulk resume upload with optimized batch processing"""
    try:
        job = Job.query.get_or_404(job_id)
        
        # Check if user has access to this job
        if not current_user.is_admin() and job.created_by != current_user.id:
            return jsonify({'error': 'Acesso negado. Você só pode fazer upload para suas próprias vagas.'}), 403
        
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
        
        # Start fast parallel processing
        if candidate_ids:
            from processors.fast_parallel_processor import start_fast_parallel_analysis
            start_fast_parallel_analysis(candidate_ids)
        
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

# Candidate management
@app.route('/candidates')
@login_required
def candidates_list():
    # Users only see candidates from their own jobs, admin sees all
    if current_user.is_admin():
        candidates = Candidate.query.order_by(Candidate.ai_score.desc().nullslast()).all()
    else:
        user_job_ids = [job.id for job in Job.query.filter_by(created_by=current_user.id)]
        candidates = Candidate.query.filter(Candidate.job_id.in_(user_job_ids)).order_by(Candidate.ai_score.desc().nullslast()).all()
    
    # Group candidates by job
    job_groups = {}
    for candidate in candidates:
        job_id = candidate.job.id
        if job_id not in job_groups:
            job_groups[job_id] = {
                'job': candidate.job,
                'candidates': []
            }
        job_groups[job_id]['candidates'].append(candidate)
    

    
    return render_template('candidates/list.html', job_groups=job_groups)

@app.route('/candidates/<int:candidate_id>')
@login_required
def candidate_detail(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    
    # Check if user has access to this candidate
    if not current_user.is_admin() and candidate.job.created_by != current_user.id:
        flash('Acesso negado. Você só pode ver candidatos das suas próprias vagas.', 'error')
        return redirect(url_for('candidates_list'))
    
    comments = CandidateComment.query.filter_by(candidate_id=candidate_id).order_by(
        CandidateComment.created_at.desc()
    ).all()
    return render_template('candidates/detail.html', candidate=candidate, comments=comments)

@app.route('/candidates/<int:candidate_id>/update_status', methods=['POST'])
@login_required
def update_candidate_status(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    
    # Check if user has access to this candidate
    if not current_user.is_admin() and candidate.job.created_by != current_user.id:
        flash('Acesso negado. Você só pode atualizar candidatos das suas próprias vagas.', 'error')
        return redirect(url_for('candidates_list'))
    
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
    
    # Check if user has access to this candidate
    if not current_user.is_admin() and candidate.job.created_by != current_user.id:
        flash('Acesso negado. Você só pode comentar em candidatos das suas próprias vagas.', 'error')
        return redirect(url_for('candidates_list'))
    
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

@app.route('/candidates/<int:candidate_id>/download')
@login_required
def download_candidate_file(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    
    # Check if user has access to this candidate
    if not current_user.is_admin() and candidate.job.created_by != current_user.id:
        flash('Acesso negado. Você só pode baixar arquivos de candidatos das suas próprias vagas.', 'error')
        return redirect(url_for('candidates_list'))
    
    # Check if file exists
    if not os.path.exists(candidate.file_path):
        flash('Arquivo não encontrado.', 'error')
        return redirect(url_for('candidate_detail', candidate_id=candidate_id))
    
    try:
        return send_file(
            candidate.file_path,
            as_attachment=True,
            download_name=candidate.filename,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        logging.error(f"Error downloading file {candidate.file_path}: {e}")
        flash('Erro ao baixar arquivo.', 'error')
        return redirect(url_for('candidate_detail', candidate_id=candidate_id))

@app.route('/candidates/<int:candidate_id>/delete', methods=['POST'])
@login_required
def delete_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    
    # Check if user has access to this candidate
    if not current_user.is_admin() and candidate.job.created_by != current_user.id:
        flash('Acesso negado. Você só pode excluir candidatos das suas próprias vagas.', 'error')
        return redirect(url_for('candidates_list'))
    
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

@app.route('/api/test-text-extraction/<int:candidate_id>')
@login_required
def test_text_extraction(candidate_id):
    """Test text extraction for debugging"""
    try:
        candidate = Candidate.query.get_or_404(candidate_id)
        
        # Check if user has access to this candidate
        if not current_user.is_admin() and candidate.job.created_by != current_user.id:
            return jsonify({'error': 'Acesso negado'}), 403
        
        from services.file_processor import extract_text_from_file
        
        # Extract text
        resume_text = extract_text_from_file(candidate.file_path, candidate.file_type)
        
        return jsonify({
            'success': True,
            'text_length': len(resume_text),
            'text_preview': resume_text[:1000],
            'file_path': candidate.file_path,
            'file_type': candidate.file_type
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/candidates/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_candidates():
    """Delete multiple candidates at once"""
    try:
        candidate_ids = request.form.getlist('candidate_ids')
        
        if not candidate_ids:
            flash('Nenhum candidato selecionado.', 'error')
            return redirect(url_for('candidates_list'))
        
        # Get candidates and check permissions
        candidates = Candidate.query.filter(Candidate.id.in_(candidate_ids)).all()
        
        if not current_user.is_admin():
            # Users can only delete candidates from their own jobs
            user_job_ids = [job.id for job in Job.query.filter_by(created_by=current_user.id)]
            candidates = [c for c in candidates if c.job_id in user_job_ids]
        
        if not candidates:
            flash('Nenhum candidato válido selecionado.', 'error')
            return redirect(url_for('candidates_list'))
        
        deleted_count = 0
        deleted_names = []
        
        for candidate in candidates:
            try:
                # Delete the file from the filesystem
                if candidate.file_path and os.path.exists(candidate.file_path):
                    os.remove(candidate.file_path)
                
                # Delete from database
                db.session.delete(candidate)
                deleted_count += 1
                deleted_names.append(candidate.name)
                
            except Exception as e:
                logging.error(f"Error deleting candidate {candidate.id}: {e}")
                continue
        
        db.session.commit()
        
        if deleted_count > 0:
            if deleted_count == 1:
                flash(f'Candidato {deleted_names[0]} excluído com sucesso!', 'success')
            else:
                flash(f'{deleted_count} candidatos excluídos com sucesso!', 'success')
        else:
            flash('Nenhum candidato foi excluído.', 'error')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir candidatos: {str(e)}', 'error')
    
    return redirect(url_for('candidates_list'))

# API endpoints for real-time updates
@app.route('/api/candidate/<int:candidate_id>/status')
@login_required
def api_candidate_status(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    
    # Check if user has access to this candidate
    if not current_user.is_admin() and candidate.job.created_by != current_user.id:
        return jsonify({'error': 'Acesso negado'}), 403
    
    return jsonify({
        'id': candidate.id,
        'analysis_status': candidate.analysis_status,
        'ai_score': candidate.ai_score,
        'status': candidate.status
    })

@app.route('/api/jobs/<int:job_id>/processing_status')
@login_required
def api_job_processing_status(job_id):
    """Get processing status for all candidates in a job"""
    try:
        job = Job.query.get_or_404(job_id)
        
        # Check if user has access to this job
        if not current_user.is_admin() and job.created_by != current_user.id:
            return jsonify({'error': 'Acesso negado'}), 403
        
        candidates = Candidate.query.filter_by(job_id=job_id).all()
        candidate_ids = [c.id for c in candidates]
        
        # Always use database status for accurate results
        status_counts = {
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0,
            'deleted': 0,
            'total': len(candidates)
        }
        
        for candidate in candidates:
            status_counts[candidate.analysis_status] += 1
        
        candidate_details = []
        
        for candidate in candidates:
            candidate_details.append({
                'id': candidate.id,
                'name': candidate.name,
                'analysis_status': candidate.analysis_status,
                'ai_score': candidate.ai_score,
                'analyzed_at': candidate.analyzed_at.isoformat() if candidate.analyzed_at else None
            })
        
        active_total = status_counts['total'] - status_counts['deleted']
        progress_percentage = round((status_counts['completed'] + status_counts['failed']) / max(active_total, 1) * 100, 1) if active_total > 0 else 0
        
        return jsonify({
            'status_counts': status_counts,
            'candidates': candidate_details,
            'progress_percentage': progress_percentage,
            'is_complete': active_total > 0 and (status_counts['completed'] + status_counts['failed']) >= active_total
        })
        
    except Exception as e:
        logging.error(f"Error getting processing status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/candidates/<int:candidate_id>/reprocess', methods=['POST'])
@login_required
def api_reprocess_candidate(candidate_id):
    """Reprocess a failed or outdated candidate"""
    try:
        logging.info(f"Reprocessamento solicitado para candidato {candidate_id}")
        
        candidate = Candidate.query.get_or_404(candidate_id)
        logging.info(f"Candidato encontrado: {candidate.name}")
        
        # Check if user has access to this candidate
        if not current_user.is_admin() and candidate.job.created_by != current_user.id:
            logging.warning(f"Acesso negado para candidato {candidate_id}")
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Check if analysis is outdated (contains generic text)
        is_outdated = False
        if candidate.ai_analysis:
            outdated_indicators = [
                "Como o currículo não foi fornecido",
                "caso você compartilhe o CV",
                "currículo hipotético",
                "João Silva",
                "Empresa XYZ",
                "Empresa ABC"
            ]
            is_outdated = any(indicator in candidate.ai_analysis for indicator in outdated_indicators)
        
        logging.info(f"Status atual: {candidate.analysis_status}, Score: {candidate.ai_score}")
        
        # Reset candidate status
        candidate.analysis_status = 'pending'
        candidate.ai_score = None
        candidate.ai_summary = None
        candidate.ai_analysis = None
        candidate.analyzed_at = None
        db.session.commit()
        
        logging.info(f"Status resetado para 'pending'")
        
        # Start fast parallel processing
        from processors.fast_parallel_processor import start_fast_parallel_analysis
        start_fast_parallel_analysis([candidate_id])
        
        logging.info(f"Processamento iniciado para candidato {candidate_id}")
        
        message = f'Candidato {candidate.name} foi colocado na fila para reprocessamento'
        if is_outdated:
            message += ' (análise antiga detectada)'
        
        return jsonify({
            'success': True,
            'message': message,
            'was_outdated': is_outdated
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
    """Manually trigger processing of pending and failed candidates"""
    try:
        # Users only process their own candidates, admin processes all
        if current_user.is_admin():
            candidates_to_process = Candidate.query.filter(
                Candidate.analysis_status.in_(['pending', 'failed'])
            ).all()
        else:
            user_job_ids = [job.id for job in Job.query.filter_by(created_by=current_user.id)]
            candidates_to_process = Candidate.query.filter(
                Candidate.job_id.in_(user_job_ids),
                Candidate.analysis_status.in_(['pending', 'failed'])
            ).all()
        
        if not candidates_to_process:
            return jsonify({'success': False, 'message': 'Nenhum candidato pendente ou com falha encontrado'})
        
        candidate_ids = [c.id for c in candidates_to_process]
        
        from processors.fast_parallel_processor import start_fast_parallel_analysis
        start_fast_parallel_analysis(candidate_ids)
        
        return jsonify({
            'success': True, 
            'message': f'Processamento iniciado para {len(candidate_ids)} candidatos (incluindo reprocessamento de falhas)',
            'candidate_ids': candidate_ids
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/jobs/<int:job_id>/reprocess-all')
@login_required
def api_reprocess_all_candidates(job_id):
    """Reprocess ALL candidates from a specific job"""
    try:
        job = Job.query.get_or_404(job_id)
        
        # Check if user has access to this job
        if not current_user.is_admin() and job.created_by != current_user.id:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Get ALL candidates from this job (regardless of status)
        candidates_to_process = Candidate.query.filter_by(job_id=job_id).all()
        
        if not candidates_to_process:
            return jsonify({'success': False, 'message': 'Nenhum candidato encontrado para esta vaga'})
        
        # Reset all candidates to pending status (including stuck ones)
        for candidate in candidates_to_process:
            candidate.analysis_status = 'pending'
            candidate.ai_score = None
            candidate.ai_summary = None
            candidate.ai_analysis = None
            candidate.analyzed_at = None
        
        db.session.commit()
        
        candidate_ids = [c.id for c in candidates_to_process]
        
        from processors.fast_parallel_processor import start_fast_parallel_analysis
        start_fast_parallel_analysis(candidate_ids)
        
        return jsonify({
            'success': True, 
            'message': f'Reanálise iniciada para {len(candidate_ids)} candidatos da vaga "{job.title}"',
            'candidate_ids': candidate_ids
        })
    except Exception as e:
        logging.error(f"Error reprocessing all candidates for job {job_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/jobs/<int:job_id>/reset-stuck')
@login_required
def api_reset_stuck_candidates(job_id):
    """Reset candidates stuck in processing status"""
    try:
        job = Job.query.get_or_404(job_id)
        
        # Check if user has access to this job
        if not current_user.is_admin() and job.created_by != current_user.id:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Find candidates stuck in processing
        stuck_candidates = Candidate.query.filter_by(
            job_id=job_id, 
            analysis_status='processing'
        ).all()
        
        if not stuck_candidates:
            return jsonify({'success': False, 'message': 'Nenhum candidato preso em processamento encontrado'})
        
        # Reset stuck candidates to pending
        for candidate in stuck_candidates:
            candidate.analysis_status = 'pending'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(stuck_candidates)} candidatos foram resetados de "processando" para "pendente"',
            'reset_count': len(stuck_candidates)
        })
        
    except Exception as e:
        logging.error(f"Error resetting stuck candidates for job {job_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})

from datetime import datetime

@app.route('/jobs/<int:job_id>/processing-monitor')
@login_required
def processing_monitor(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('jobs/processing_monitor.html', job=job)
