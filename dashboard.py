from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import json
import time
import matplotlib.pyplot as plt
import io
import base64
from collections import Counter
import threading

app = Flask(__name__)

# Configuration du serveur principal
MAIN_SERVER_URL = "http://localhost:5000"

# Variables globales pour stocker les résultats
analysis_results = None
processing = False

def create_sentiment_chart(sentiment_distribution):
    """Crée un graphique camembert pour les sentiments"""
    labels = list(sentiment_distribution.keys())
    sizes = list(sentiment_distribution.values())
    colors = ['#ff9999', '#66b3ff', '#99ff99']  # rouge, bleu, vert
    
    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, colors=colors[:len(labels)], autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title('Distribution des Sentiments')
    
    # Convertir en image base64
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return f"data:image/png;base64,{chart_url}"

def create_platform_chart(platform_distribution):
    """Crée un graphique barres pour les plateformes"""
    platforms = list(platform_distribution.keys())
    counts = list(platform_distribution.values())
    colors = ['#1da1f2', '#1877f2', '#e4405f']  # Twitter blue, Facebook blue, Instagram pink
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(platforms, counts, color=colors[:len(platforms)])
    plt.title('Répartition par Plateforme')
    plt.xlabel('Plateformes')
    plt.ylabel('Nombre de commentaires')
    
    # Ajouter les valeurs sur les barres
    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(count), ha='center', va='bottom')
    
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return f"data:image/png;base64,{chart_url}"

def create_keywords_chart(top_keywords):
    """Crée un graphique horizontal pour les mots-clés"""
    if not top_keywords:
        return None
        
    keywords = list(top_keywords.keys())[:10]  # Top 10 seulement
    counts = list(top_keywords.values())[:10]
    
    plt.figure(figsize=(10, 8))
    bars = plt.barh(keywords, counts, color='skyblue')
    plt.title('Top 10 des Mots-Clés Mentionnés')
    plt.xlabel('Nombre de mentions')
    
    # Ajouter les valeurs sur les barres
    for bar, count in zip(bars, counts):
        plt.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                str(count), ha='left', va='center')
    
    plt.gca().invert_yaxis()  # Afficher le plus grand en haut
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return f"data:image/png;base64,{chart_url}"

def get_sentiment_emoji(sentiment):
    """Retourne un emoji pour le sentiment"""
    emojis = {
        'positive': '😊',
        'negative': '😠', 
        'neutral': '😐'
    }
    return emojis.get(sentiment, '❓')

def get_platform_icon(platform):
    """Retourne une icône pour la plateforme"""
    icons = {
        'twitter': '🐦',
        'facebook': '📘',
        'instagram': '📸'
    }
    return icons.get(platform, '📱')

def launch_analysis_thread():
    """Lance l'analyse en arrière-plan"""
    global processing, analysis_results
    
    try:
        print("🚀 Lancement de l'analyse MapReduce...")
        response = requests.get(f"{MAIN_SERVER_URL}/api/analyze", timeout=120)
        
        if response.status_code == 200:
            analysis_results = response.json()
            print("✅ Analyse terminée avec succès")
        else:
            analysis_results = {'error': f"Erreur du serveur: {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        analysis_results = {'error': f"Erreur de connexion: {str(e)}"}
    except Exception as e:
        analysis_results = {'error': f"Erreur inattendue: {str(e)}"}
    finally:
        processing = False

@app.route('/')
def index():
    """Page principale du dashboard"""
    global analysis_results, processing
    
    # Vérifier la connexion au serveur principal
    try:
        health_response = requests.get(f"{MAIN_SERVER_URL}/health", timeout=5)
        server_healthy = health_response.status_code == 200
    except:
        server_healthy = False
    
    # Récupérer les statistiques des données
    try:
        stats_response = requests.get(f"{MAIN_SERVER_URL}/api/stats", timeout=5)
        if stats_response.status_code == 200:
            data_stats = stats_response.json()
        else:
            data_stats = None
    except:
        data_stats = None
    
    # Préparer les données pour le template
    charts = {}
    summary = {}
    
    if analysis_results and 'analysis' in analysis_results:
        analysis_data = analysis_results['analysis']
        
        # Créer les graphiques
        charts['sentiment'] = create_sentiment_chart(analysis_data.get('sentiment_distribution', {}))
        charts['platform'] = create_platform_chart(analysis_data.get('platform_distribution', {}))
        charts['keywords'] = create_keywords_chart(analysis_data.get('top_keywords', {}))
        
        # Préparer le résumé
        summary = {
            'total_comments': analysis_data.get('total_comments_analyzed', 0),
            'overall_sentiment': analysis_data.get('overall_sentiment', 'unknown'),
            'processing_time': analysis_results.get('processing_time', 0),
            'distributed': analysis_results.get('distributed_processing', False)
        }
    
    return render_template('dashboard.html',
                         results=analysis_results,
                         processing=processing,
                         server_healthy=server_healthy,
                         data_stats=data_stats,
                         charts=charts,
                         summary=summary,
                         get_sentiment_emoji=get_sentiment_emoji,
                         get_platform_icon=get_platform_icon)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Lance l'analyse des sentiments"""
    global processing
    
    if processing:
        return jsonify({'error': 'Une analyse est déjà en cours'}), 400
    
    processing = True
    
    # Lancer l'analyse dans un thread séparé
    thread = threading.Thread(target=launch_analysis_thread)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Analyse lancée avec succès'})

@app.route('/status')
def status():
    """Endpoint pour vérifier le statut de l'analyse"""
    global processing, analysis_results
    
    return jsonify({
        'processing': processing,
        'has_results': analysis_results is not None,
        'results': analysis_results if analysis_results else None
    })

@app.route('/clear')
def clear_results():
    """Efface les résultats actuels"""
    global analysis_results
    analysis_results = None
    return redirect(url_for('index'))

@app.route('/test_connection')
def test_connection():
    """Teste la connexion au serveur principal"""
    try:
        response = requests.get(f"{MAIN_SERVER_URL}/health", timeout=5)
        return jsonify({
            'connected': response.status_code == 200,
            'status': response.json() if response.status_code == 200 else {'error': 'Connection failed'}
        })
    except Exception as e:
        return jsonify({'connected': False, 'error': str(e)})

if __name__ == '__main__':
    print("🌐 Dashboard d'Analyse de Sentiments")
    print("📍 URL: http://localhost:5001")
    print("📊 Accès au dashboard via votre navigateur")
    
    app.run(host='0.0.0.0', port=5001, debug=True)