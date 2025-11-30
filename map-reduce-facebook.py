from flask import Flask, request, jsonify
from collections import Counter

app = Flask(__name__)

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

def map_sentiment_analysis(comments_chunk):
    """Fonction Map: Analyse le sentiment d'un groupe de commentaires"""
    sentiment_count = Counter()
    platform_stats = Counter()
    keyword_mentions = Counter()
    
    for comment in comments_chunk:
        text = comment['text'].lower()
        
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

@app.route('/analyze', methods=['POST'])
def analyze_facebook_comments():
    """Endpoint pour analyser les commentaires Facebook"""
    data = request.get_json()
    comments = data.get('comments', [])
    
    print(f"📘 Nœud Facebook: traitement de {len(comments)} commentaires...")
    
    result = map_sentiment_analysis(comments)
    
    print(f"✅ Nœud Facebook: analyse terminée - {result['comments_processed']} commentaires traités")
    
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'node': 'facebook_processor'})

if __name__ == '__main__':
    print("📘 Nœud Facebook d'Analyse de Sentiments démarré")
    print("📍 Port: 5002")
    print("📊 Responsable: Traitement des commentaires Facebook") 
    
    app.run(host='0.0.0.0', port=5002, debug=True)