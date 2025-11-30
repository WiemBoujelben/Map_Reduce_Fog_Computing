from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import time
import json
from collections import Counter

app = Flask(__name__)
CORS(app)

# ⚠️ REMPLACEZ CES IP PAR LES VOTRES ⚠️
NODE_2_URL = "http://10.250.196.36:5001"  # Machine 2 - Twitter
NODE_3_URL = "http://10.250.196.154:5002"  # Machine 3 - Facebook

# Listes de mots pour l'analyse de sentiment
POSITIVE_WORDS = {
    'bon', 'excellent', 'génial', 'super', 'aimer', 'adorer', 'parfait', 'fantastique',
    'heureux', 'content', 'satisfait', 'recommande', 'exceptionnel', 'professionnel',
    'rapide', 'conforme', 'intuitif', 'innovant', 'bravo', 'competent', 'ravis'
}

NEGATIVE_WORDS = {
    'mauvais', 'horrible', 'nul', 'détester', 'pas', 'probleme', 'colère', 'triste',
    'deçu', 'énervé', 'déçu', 'endommagé', 'médiocre', 'tard', 'inacceptable',
    'incompréhensible', 'difficile', 'manquant', 'injoignable', 'frustrant', 'scandaleux'
}

def load_comments():
    """Charge les commentaires depuis le fichier JSON"""
    try:
        with open('comments.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['comments']
    except FileNotFoundError:
        print("❌ Fichier comments.json non trouvé")
        return []

def divide_comments_by_platform(comments):
    """Divise les commentaires par plateforme"""
    twitter_comments = []
    facebook_comments = []
    instagram_comments = []
    
    for comment in comments:
        if comment['platform'] == 'twitter':
            twitter_comments.append(comment)
        elif comment['platform'] == 'facebook':
            facebook_comments.append(comment)
        elif comment['platform'] == 'instagram':
            instagram_comments.append(comment)
    
    return twitter_comments, facebook_comments, instagram_comments

def map_sentiment_analysis(comments_chunk):
    """Fonction Map: Analyse le sentiment d'un groupe de commentaires"""
    sentiment_count = Counter()
    platform_stats = Counter()
    keyword_mentions = Counter()
    
    for comment in comments_chunk:
        text = comment['text'].lower()
        
        # Analyse de sentiment basique
        positive_score = sum(1 for word in POSITIVE_WORDS if word in text)
        negative_score = sum(1 for word in NEGATIVE_WORDS if word in text)
        
        if positive_score > negative_score:
            sentiment = 'positive'
        elif negative_score > positive_score:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        sentiment_count[sentiment] += 1
        platform_stats[comment['platform']] += 1
        
        # Compter les mentions de mots-clés importants
        keywords = ['produit', 'service', 'client', 'livraison', 'qualité', 'prix', 'commande']
        for keyword in keywords:
            if keyword in text:
                keyword_mentions[keyword] += 1
    
    return {
        'sentiments': dict(sentiment_count),
        'platform_stats': dict(platform_stats),
        'keyword_mentions': dict(keyword_mentions),
        'comments_processed': len(comments_chunk)
    }

def reduce_sentiment_analysis(results):
    """Fonction Reduce: Fusionne l'analyse de tous les nœuds"""
    global_sentiments = Counter()
    global_platforms = Counter()
    global_keywords = Counter()
    total_comments = 0
    
    for result in results:
        total_comments += result['comments_processed']
        global_sentiments.update(result['sentiments'])
        global_platforms.update(result['platform_stats'])
        global_keywords.update(result['keyword_mentions'])
    
    # Calcul des pourcentages
    sentiment_percentages = {}
    for sentiment, count in global_sentiments.items():
        sentiment_percentages[sentiment] = round((count / total_comments) * 100, 2)
    
    # Sentiment global dominant
    overall_sentiment = global_sentiments.most_common(1)[0][0] if global_sentiments else 'neutral'
    
    return {
        'sentiment_distribution': sentiment_percentages,
        'platform_distribution': dict(global_platforms),
        'top_keywords': dict(global_keywords.most_common(10)),
        'total_comments_analyzed': total_comments,
        'overall_sentiment': overall_sentiment
    }

def send_to_machine(url, data):
    """Envoie des données à un nœud distant avec gestion d'erreur"""
    try:
        print(f"📤 Envoi de {len(data)} commentaires à {url}")
        response = requests.post(f"{url}/analyze", json={'comments': data}, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur avec {url}: {e}")
        # Fallback: traiter localement
        print("🔄 Traitement local en fallback...")
        return map_sentiment_analysis(data)

@app.route('/api/analyze', methods=['POST', 'GET'])
def analyze_sentiments():
    """Endpoint principal pour lancer l'analyse"""
    start_time = time.time()
    
    # Charger les commentaires
    all_comments = load_comments()
    
    if not all_comments:
        return jsonify({'error': 'Aucun commentaire trouvé'}), 400
    
    print(f"📊 Analyse de {len(all_comments)} commentaires...")
    
    # Division des commentaires par plateforme
    twitter_comments, facebook_comments, instagram_comments = divide_comments_by_platform(all_comments)
    
    print(f"🔀 Répartition:")
    print(f"   Twitter: {len(twitter_comments)} commentaires")
    print(f"   Facebook: {len(facebook_comments)} commentaires") 
    print(f"   Instagram: {len(instagram_comments)} commentaires")
    
    # Traitement distribué
    print("🚀 Lancement du traitement MapReduce...")
    
    # Nœud 1 traite Instagram (local)
    local_result = map_sentiment_analysis(instagram_comments)
    print("✅ Nœud 1 (Instagram) terminé")
    
    # Nœud 2 traite Twitter (distant)
    twitter_result = send_to_machine(NODE_2_URL, twitter_comments)
    print("✅ Nœud 2 (Twitter) terminé")
    
    # Nœud 3 traite Facebook (distant)  
    facebook_result = send_to_machine(NODE_3_URL, facebook_comments)
    print("✅ Nœud 3 (Facebook) terminé")
    
    # Fusion des résultats
    print("🔄 Fusion des résultats...")
    final_analysis = reduce_sentiment_analysis([local_result, twitter_result, facebook_result])
    
    execution_time = round(time.time() - start_time, 2)
    
    print(f"🎉 Analyse terminée en {execution_time}s")
    
    return jsonify({
        'analysis': final_analysis,
        'processing_time': execution_time,
        'distributed_processing': True
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Endpoint pour voir les statistiques des données"""
    comments = load_comments()
    platform_count = Counter()
    
    for comment in comments:
        platform_count[comment['platform']] += 1
    
    return jsonify({
        'total_comments': len(comments),
        'platform_distribution': dict(platform_count)
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'service': 'main_sentiment_analyzer',
        'nodes_configured': [NODE_2_URL, NODE_3_URL]
    })

if __name__ == '__main__':
    print("🚀 Serveur Principal d'Analyse de Sentiments")
    print("📍 URLs des nœuds distants:")
    print(f"   Nœud 2 (Twitter): {NODE_2_URL}")
    print(f"   Nœud 3 (Facebook): {NODE_3_URL}")
    print("📊 Endpoints disponibles:")
    print("   GET /health - Vérification du statut")
    print("   GET /api/stats - Statistiques des données") 
    print("   POST/GET /api/analyze - Lancer l'analyse complète")
    print("\n⚠️  ASSUREZ-VOUS QUE LES MACHINES 2 ET 3 SONT ALLUMÉES ET CONFIGURÉES")
    
    app.run(host='0.0.0.0', port=5000, debug=True)