from flask import Flask, render_template, jsonify
import numpy as np
import os
from datetime import datetime, timedelta

app = Flask(__name__)

class GridBoosterSimulation:
    def __init__(self):
        # Parámetros de configuración del sistema
        self.power_max = 500  # MW - Capacidad máxima del BESS
        self.ramp_rate = 50   # MW/s - Tasa de rampa
        self.activation_delay = 0.1  # segundos - Retardo de activación
        self.base_power = 1700  # MW - Potencia base del sistema
        
    def simulate_contingency(self, duration_seconds=15):
        """
        Simula una contingencia y la respuesta del Grid Booster.
        
        Args:
            duration_seconds (int): Duración de la simulación en segundos
            
        Returns:
            dict: Diccionario con los resultados de la simulación
        """
        # Crear puntos de tiempo para la simulación
        time_points = np.linspace(0, duration_seconds, duration_seconds * 10)
        
        # Inicializar arrays para almacenar resultados
        base_power = np.ones(len(time_points)) * self.base_power
        gb_response = np.zeros(len(time_points))
        
        # Simular falla en t=2s
        fault_idx = np.where(time_points >= 2)[0][0]
        base_power[fault_idx:] *= 0.6  # Caída al 60% después de la falla
        
        # Simular respuesta del Grid Booster
        activation_idx = np.where(time_points >= (2 + self.activation_delay))[0][0]
        
        # Aplicar rampa de potencia
        for i in range(activation_idx, len(time_points)):
            time_since_activation = time_points[i] - time_points[activation_idx]
            target_power = min(self.ramp_rate * time_since_activation, self.power_max)
            gb_response[i] = target_power
        
        # Calcular potencia total
        total_power = base_power + gb_response
        
        return {
            'time': time_points.tolist(),
            'base_power': base_power.tolist(),
            'gb_response': gb_response.tolist(),
            'total_power': total_power.tolist(),
            'timestamp': datetime.now().isoformat()
        }

    def get_system_status(self):
        """
        Obtiene el estado actual del sistema.
        
        Returns:
            dict: Estado actual del sistema
        """
        return {
            'power_max': self.power_max,
            'ramp_rate': self.ramp_rate,
            'activation_delay': self.activation_delay,
            'base_power': self.base_power,
            'status': 'operational'
        }

# Crear instancia del simulador
simulator = GridBoosterSimulation()

@app.route('/')
def home():
    """Ruta principal que renderiza la interfaz de usuario"""
    return render_template('index.html')

@app.route('/api/simulate')
def simulate():
    """Endpoint API para obtener datos de simulación"""
    try:
        return jsonify(simulator.simulate_contingency())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def status():
    """Endpoint API para obtener el estado del sistema"""
    try:
        return jsonify(simulator.get_system_status())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Obtener puerto del entorno o usar 5000 por defecto
    port = int(os.environ.get('PORT', 5000))
    # Ejecutar la aplicación
    app.run(host='0.0.0.0', port=port)