import mysql.connector
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import numpy as np

DB_HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASSWORD = 'hw5password123'
DB_NAME = 'requests'

def load_data():
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT client_ip, country FROM ip_country_mapping WHERE country IS NOT NULL AND country != ''")
    data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    ips = [row[0] for row in data]
    countries = [row[1] for row in data]
    
    return ips, countries

def ip_to_features(ip):
    parts = ip.split('.')
    return [int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])]

def train_model():
    print("loading data...")
    ips, countries = load_data()
    
    print(f"total samples: {len(ips)}")
    
    X = np.array([ip_to_features(ip) for ip in ips])
    
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(countries)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"training samples: {len(X_train)}")
    print(f"test samples: {len(X_test)}")
    print(f"unique countries: {len(label_encoder.classes_)}")
    
    print("\ntraining random forest model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    predictions = model.predict(X_test)
    
    correct = sum([1 for p, a in zip(predictions, y_test) if p == a])
    accuracy = correct / len(y_test) * 100
    
    print(f"\nmodel 1: ip to country prediction")
    print(f"accuracy: {accuracy:.2f}%")
    print(f"correct: {correct}/{len(y_test)}")
    
    with open('model1_results.txt', 'w') as f:
        f.write(f"model 1: ip to country prediction (random forest)\n")
        f.write(f"accuracy: {accuracy:.2f}%\n")
        f.write(f"correct predictions: {correct}/{len(y_test)}\n")
        f.write(f"training samples: {len(X_train)}\n")
        f.write(f"test samples: {len(X_test)}\n")
        f.write(f"unique countries: {len(label_encoder.classes_)}\n")
        f.write(f"\nsample predictions:\n")
        for i in range(min(10, len(X_test))):
            pred_country = label_encoder.inverse_transform([predictions[i]])[0]
            true_country = label_encoder.inverse_transform([y_test[i]])[0]
            match = "✓" if predictions[i] == y_test[i] else "✗"
            f.write(f"  {match} actual: {true_country}, predicted: {pred_country}\n")
    
    print("results saved to model1_results.txt")
    
    return accuracy

if __name__ == '__main__':
    accuracy = train_model()
    if accuracy < 99:
        print(f"warning: accuracy {accuracy:.2f}% is below 99% requirement")
    else:
        print(f"success: accuracy meets 99% requirement")