import json
import random

positive_phrases = [
    "J adore ce produit ! Excellent qualité",
    "Super satisfaction, je recommande vivement", 
    "Service client exceptionnel, très professionnel",
    "Livraison ultra rapide, emballage parfait",
    "Produit conforme à la description, très content",
    "Rapport qualité-prix excellent, bon achat",
    "Facile à utiliser, interface intuitive",
    "Belle finition, attention aux détails",
    "Fonctionnalités innovantes, bravo à l'équipe",
    "Soutien technique réactif et compétent"
]

negative_phrases = [
    "Très déçu, produit ne fonctionne pas",
    "Service client horrible, réponse tardive", 
    "Livraison en retard de 3 jours, inacceptable",
    "Produit endommagé à la réception",
    "Qualité médiocre, pas du tout satisfait",
    "Prix trop élevé pour ce que c'est",
    "Instructions incompréhensibles, difficile à installer",
    "Fonctionnalités manquantes par rapport à la pub", 
    "Support technique injoignable, frustrant",
    "Commande annulée sans explication"
]

neutral_phrases = [
    "Produit correct, sans plus",
    "Dans la moyenne, ni bon ni mauvais",
    "Fonctionne mais pourrait être mieux", 
    "Acceptable pour le prix payé",
    "Sans problème particulier",
    "Correspond à mes attentes basiques",
    "Utilisation simple, interface basique",
    "Livraison dans les délais standards"
]

platforms = ["twitter", "facebook", "instagram"]

def generate_comments(num_comments=1000):
    comments = []
    
    for i in range(num_comments):
        # Répartition: 40% positif, 35% négatif, 25% neutre
        rand = random.random()
        if rand < 0.40:
            phrase = random.choice(positive_phrases)
        elif rand < 0.75:
            phrase = random.choice(negative_phrases) 
        else:
            phrase = random.choice(neutral_phrases)
        
        platform = random.choice(platforms)
        
        # Ajouter des variations
        variations = ["", "!", "!!", "...", " 👍", " 😊", " 😠", " 👎", " 💯", " ❤️"]
        text = phrase + random.choice(variations)
        
        comments.append({
            "id": i + 1,
            "platform": platform,
            "text": text
        })
    
    return comments

comments = generate_comments(1000000)
data = {"comments": comments}

with open('comments.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ 1000 commentaires générés dans comments.json")
print(f"📊 Répartition par plateforme:")
platform_count = {}
for comment in comments:
    platform = comment['platform']
    platform_count[platform] = platform_count.get(platform, 0) + 1

for platform, count in platform_count.items():
    print(f"   {platform}: {count} commentaires")

input("Appuyez sur Entrée pour continuer...")