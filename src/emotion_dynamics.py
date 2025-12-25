class EmotionDynamics:
    def __init__(self, decay_rate: float = 0.8, pitch_sensitivity: float = 5.0, speed_sensitivity: float = 0.2):
        """
        :param decay_rate: Rate at which values return to baseline (0.0-1.0).
        :param pitch_sensitivity: Magnitude of pitch shift per unit of uncertainty.
        :param speed_sensitivity: Magnitude of speed shift per unit of entropy.
        """
        self.pitch_val = 0.0 # Delta pitch (semitones approx or proprietary scale)
        self.speed_val = 0.0 # Delta speed (length multiplier addend. 0.0 = no change)
        
        self.decay_rate = decay_rate
        self.pitch_sensitivity = pitch_sensitivity
        self.speed_sensitivity = speed_sensitivity

    def update(self, confidence: float, entropy: float):
        """
        Update the emotional state based on new token metrics.
        confidence: 0.0 (Unsure) to 1.0 (Sure)
        entropy: 0.0 (Clear) to High (Confused)
        """
        # Decay step: Move towards 0.0
        self.pitch_val *= self.decay_rate
        self.speed_val *= self.decay_rate
        
        # Impact calculation
        # Logic: 
        # - Low Confidence (Unsure) -> Variance in Pitch. 
        #   Let's simply drop pitch for uncertainty (mumbling) or maybe raise it?
        #   Let's try: Unsure -> Lower pitch (Lack of assertion).
        #   Impact = (1.0 - confidence)
        
        pitch_impact = (1.0 - confidence) * self.pitch_sensitivity
        # Make the direction alternate or depend on something else? 
        # For simple physics: Uncertainty pushes pitch DOWN (or away from center).
        # Let's subtract impact to lower pitch.
        self.pitch_val -= pitch_impact
        
        # - High Entropy (Confused) -> Slower speaking (Longer duration)
        #   Speed val is added to 'length' (so >0 means slower/longer)?
        #   Or added to 'speedScale' (so >0 means faster)?
        #   Let's assume speed_val is "Time Dilation". Positive = Slower.
        #   Impact = entropy
        
        speed_impact = entropy * self.speed_sensitivity
        self.speed_val += speed_impact
        
        return {
            "pitch_delta": self.pitch_val,
            "speed_delta": self.speed_val
        }

    def reset(self):
        self.pitch_val = 0.0
        self.speed_val = 0.0
