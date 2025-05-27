import React from 'react';
import MapDisplay from './components/MapDisplay'; // Importar o componente do mapa
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header" style={{padding: '10px 0', textAlign: 'center'}}>
        <h1>Visualizador de Rota - Maricá</h1>
      </header>
      <main style={{padding: '10px'}}>
        <MapDisplay />
      </main>
    </div>
  );
}

export default App;