import glob
import os
from grammaire import lire_grammaire, chomsky  

def generer_mots(grammaire, longueur_max, max_recursion):
    """
    Génère tous les mots possibles de longueur <= longueur_max à partir de la grammaire donnée.
    """
    mots = set()

    if grammaire.axiome is None or grammaire.axiome not in grammaire.regles:
        raise ValueError("L'axiome de la grammaire n'est pas défini ou valide.")

    def derive(sequence, profondeur):
        # Limite de récursion ou de longueur atteinte
        if profondeur == 0 or len(sequence) > longueur_max:
            return
        # Si la séquence ne contient que des terminaux, ajouter le mot au set
        if all(symbol.islower() for symbol in sequence):
            mots.add(''.join(sequence))
            return
        # Sinon, remplacer les non-terminaux
        for i, symbol in enumerate(sequence):
            if symbol.isupper():  # Si c'est un non-terminal
                for prod in grammaire.regles.get(symbol, []):
                    nouvelle_sequence = sequence[:i] + prod + sequence[i+1:]
                    derive(nouvelle_sequence, profondeur - 1)

    # Lancer la dérivation à partir de l'axiome
    derive([grammaire.axiome], max_recursion)
    return sorted(mots)  


def traiter_fichiers():
    """
    Traite chaque fichier .general dans le répertoire 'examples',
    génère les mots avant et après transformation en CNF,
    puis écrit les résultats dans des fichiers .res et .mots respectivement.
    """
    # Trouver tous les fichiers .general dans le répertoire examples
    fichiers = glob.glob("examples/*.general")
    os.makedirs("test_resultat", exist_ok=True)  # Créer le répertoire pour les résultats

    for fichier in fichiers:
        # Lire la grammaire depuis le fichier .general
        grammaire = lire_grammaire(fichier)
        base_name = os.path.basename(fichier).rsplit('.', 1)[0]  # Obtenir le nom de base du fichier

        # Longueur maximale des mots générés
        longueur_max = 5

        # Étape 1 : Générer les mots à partir de la grammaire initiale
        mots_origine = generer_mots(grammaire, longueur_max, 100)
        res_file = os.path.join("test_resultat", base_name + '.res')  # Fichier .res
        with open(res_file, 'w') as f:
            f.write("\n".join(mots_origine))  # Écrire les mots dans le fichier

        # Étape 2 : Transformer la grammaire en CNF
        grammaire_cnf = chomsky(grammaire)

        # Étape 3 : Générer les mots à partir de la grammaire transformée
        mots_cnf = generer_mots(grammaire_cnf, longueur_max, 100)
        mots_file = os.path.join("test_resultat", base_name + '.mots')  # Fichier .mots
        with open(mots_file, 'w') as f:
            f.write("\n".join(mots_cnf))  # Écrire les mots dans le fichier

        # Les fichiers .res (avant transformation) et .mots (après transformation)
        # peuvent maintenant être comparés pour vérifier la cohérence.

if __name__ == "__main__":
    traiter_fichiers()
