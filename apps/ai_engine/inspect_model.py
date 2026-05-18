import pickle
import sys

def inspect_model():
    path = 'backend/apps/ai_engine/model/xgb_risk_model.pkl'
    with open(path, 'rb') as f:
        data = pickle.load(f)
    print("Keys in pickle:", data.keys())
    model = data.get('model')
    print("Model type:", type(model))
    
    if hasattr(model, 'feature_names_in_'):
        print("feature_names_in_:", model.feature_names_in_)
    elif hasattr(model, 'get_booster'):
        booster = model.get_booster()
        print("booster.feature_names:", booster.feature_names)
        
    print("n_features_in_:", getattr(model, 'n_features_in_', None))

if __name__ == '__main__':
    inspect_model()
