import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import Login from './login.tsx'
import DashBoard from './components/abas/Dashboard.tsx'
import Financeiro from './components/abas/Financeiro.tsx'
import Saldo from './components/abas/Saldo.tsx'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { Bounce, Flip, Slide, ToastContainer } from 'react-toastify'
import './index.css'
const router = createBrowserRouter([
  {
    path: '/',
    element: <Login />
  },
  {
    path: '/dashboard',
    element: <DashBoard />
  },
  {
    path: '/financeiro',
    element: <Financeiro />
  },
  {
    path: '/saldo',
    element: <Saldo />
  }
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
    <ToastContainer
      position="top-right"
      autoClose={3000}
      transition={Slide}
      closeOnClick={true}
      limit={1}
      toastClassName={(context) => {
        const baseClasses = "relative flex p-4 mx-auto text-white text-md md:text-md font-poppins rounded-2xl justify-between overflow-hidden cursor-pointer backdrop-blur-md mb-3 font-poppins";
        switch (context?.type) {
          case 'success':
            return `${baseClasses} bg-blue-950/80 border border-blue-500/40 shadow-lg shadow-blue-500/20 text-blue-100`;

          case 'error':
            return `${baseClasses} bg-red-950/80 border border-red-500/40 shadow-lg shadow-red-500/20 text-red-100`;
          default:
            return `${baseClasses} min-h-12 w-40 md:w-50  bg-slate-900/90 border border-slate-700`;
        }
      }}
    />
  </StrictMode>,
)
