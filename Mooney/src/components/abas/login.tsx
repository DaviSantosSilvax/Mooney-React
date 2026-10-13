import '../../App.css';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Mail, Lock } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'react-toastify';
import { ToastSucess } from '../Toasts/ToastSucess'
import Estrelas from '../Temas/Stars'
import { useNavigate } from 'react-router-dom';


export default function Login() {

    const navigate = useNavigate()

    const loginSchema = z.object({
        email: z.string().email("email invalido").nonempty("email é obrigatorio").refine((email) => {
            return email.endsWith("@gmail.com")
        }, "Email Invalido"
        ),
        senha: z.string().nonempty("senha é obrigatoria").min(6, "senha deve ter pelo menos 6 caracteres")
        ,
    }).refine((data) => {
        return data.email === "admin@gmail.com" && data.senha === "123456";
    }, { message: "E-mail ou senha incorretos!", path: ["email"] })
    type CreateUserFormData = z.infer<typeof loginSchema>

    const { handleSubmit, register, formState: { errors } } = useForm<CreateUserFormData>({
        resolver: zodResolver(loginSchema)

    })


    function hs(data: any) {
        toast.success("Logou com sucesso!", {
            autoClose: 2500,
        });
        setTimeout(() => {
            navigate("/dashboard");
        }, 800);
    }


    function hsError(errors: any) {
        if (errors.email) {
            toast.error(errors.email.message)
        }
        if (errors.senha) {
            toast.error(errors.senha.message)
        }
    }


    return (
        <div className="min-h-screen w-full relative overflow-hidden bg-[linear-gradient(0deg,#2727E7_20%,#000854,rgba(43,0,84,1))] flex flex-col items-center justify-center">
            <Estrelas
                density={1}
                glowIntensity={0.1}
                rotationSpeed={0.025}

                mouseRepulsion={false}
                speed={0.001}
            />



            <div className="lua-gigante absolute -top-50 left-10  z-10 md:-top-50 md:-right-0 md:left-[50vw]"></div>

            <div className='md:gap-5 gap-3 rounded-3xl border-[1px] border-[#4b05e4] flex flex-col items-center z-299 md:w-150 w-94 md:h-150 h-125 rounded-5xl relative shadow-xl shadow-blue-600/50 bg-[linear-gradient(0deg,rgba(45,0,89,0.5),rgba(1,0,3,0.5))] backdrop-blur-[2px]'>
                <div className="mt-20 text-5xl md:text-6xl font-black font-orbitron tracking-[0.25em] text-transparent bg-clip-text bg-gradient-to-b from-white via-blue-100 to-indigo-300 drop-shadow-[0_0_25px_rgba(90,140,255,0.6)] select-none uppercase">
                    Mooney
                </div>
                <div className="text-blue-400/90 text-sm md:text-base font-semibold font-poppins tracking-widest uppercase mt-1">
                    Acesso ao Portal
                </div>
                <form className="flex flex-col items-center gap-5 mt-2"
                    onSubmit={handleSubmit(hs, hsError)}
                >
                    <div className='md:w-120 md:h-14 w-80 h-14 flex flex-row border-1 rounded-[5vw] md:rounded-[1vw] mt-5 border-blue-500/10 bg-blue-500/20
                    '>

                        <Mail className="text-blue-500/50 ml-2 mt-3" size={30} /> <div className="flex flex-col">
                            <label className=" ml-5 text-blue-500/90 text-md font-poppins">
                                E-mail
                            </label>
                            <input className="ml-7 text-white outline-none bg-transparent"
                                type="email"
                                {...register('email')}


                            />

                        </div>

                    </div>
                    <div className='md:w-120 md:h-14 w-80 h-14 flex flex-row border-1 rounded-[5vw] md:rounded-[1vw] mt-5 border-blue-500/10 bg-blue-500/20'>


                        <Lock className="text-blue-500/50 ml-2 mt-3" size={30} /> <div className="flex flex-col">
                            <label className="ml-3 text-blue-500/90 text-md font-poppins">
                                Senha
                            </label>
                            <input className="ml-7 text-white outline-none bg-transparent"
                                type='password'
                                {...register('senha')}
                            />

                        </div>
                    </div>
                    <button className="md:w-60 md:text-2xl w-30 h-10 border-1 rounded-[5vw] md:rounded-[1vw] mt-5 border-blue-500/10 bg-[rgba(54,0,200,0.38)] hover:bg-[rgba(66,0,248,0.76)] hover:scale-105 transition hover:text-white text-blue-500 cursor-pointer"
                        type="submit">
                        Login</button>


                </form >

                <h1 className='text-center text-white font-bold font-poppins mt-5'>
                </h1>
            </div >

        </div >
    )
}