import './App.css';
import MainLayout from "./components/layout/MainLayout";
import AppRoutes from './routes/AppRoutes';

function App() {

  return (
    <MainLayout>
      <AppRoutes />
    </MainLayout>
  )
}

export default App
