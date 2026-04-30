import { useEffect } from 'react';
import { ModelBuilder } from './components/modelbuilder/ModelBuilder';
import { useAppStore } from './store/useAppStore';
import './App.css';

function App() {
  const theme = useAppStore((s) => s.theme);

  // Apply persisted theme to the document root on mount and whenever it changes
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <div className="app">
      <ModelBuilder />
    </div>
  );
}

export default App;
