import React from 'react';
import MapDisplayWithClickHandler from './components/MapDisplay'; // Importe o MapDisplay (ou MapDisplayWithClickHandler)
import './App.css'; // Ou qualquer CSS que você tenha

function App() {
  return (
    <div className="App">
      <header className="App-header" style={{padding: '10px 0', textAlign: 'center'}}>
        <h1>Visualizador de Rota - Maricá</h1>
      </header>
      <main style={{padding: '10px'}}>
        <MapDisplayWithClickHandler />
      </main>
    </div>
  );
}

export default App;