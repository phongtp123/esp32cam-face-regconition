import numpy as np

class DecisionStump:
    def __init__(self, feature=None, threshold=0.0, polarity=1, amountOfSay=0.0):
        self.feature = feature
        self.threshold = threshold
        self.polarity = polarity
        self.amountOfSay = amountOfSay

    def predict(self, feature_column):
        preds = np.ones_like(feature_column)
        preds[self.polarity * feature_column < self.polarity * self.threshold] = 1
        preds[self.polarity * feature_column >= self.polarity * self.threshold] = -1
        return preds