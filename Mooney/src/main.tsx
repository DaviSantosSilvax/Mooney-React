import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import Login from './components/abas/login.tsx'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
const router = createBrowserRouter([
  {
    path: '/',
    element: <Login />
  }
])
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
