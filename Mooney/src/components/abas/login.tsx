import '../../App.css';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Mail, Lock } from 'lucide-react';

const loginSchema = z.object({
    email: z.string().email("Email Inválido!!!").min(1, "Email Obrigatório!!"),
    senha: z.string().min(6, "A senha precisar de 6 Caracteres!!")
})

type LoginFormData = z.infer<typeof loginSchema>;

export default function Login() {

    const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>({
        resolver: zodResolver(loginSchema)
    });
    function loginSucesso(data: LoginFormData) {
        console.log("Tudo Certo", data.email, data.senha);
    }

    return (
        <div className="min-h-screen w-full relative overflow-hidden bg-[linear-gradient(0deg,rgba(2,0,36,1)_20%,rgba(0,0,46,1),rgba(43,0,84,1))] flex flex-col items-center justify-center">

            {/* Céu Estrelado Responsivo */}
            <div className="absolute inset-0 pointer-events-none z-0">
                <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
                    <filter id="star-glow">
                        <feGaussianBlur stdDeviation="1" result="blur" />
                        <feMerge>
                            <feMergeNode in="blur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                    <g fill="white">
                        <circle cx="10%" cy="20%" r="1" opacity="0.6" />
                        <circle cx="25%" cy="65%" r="2" filter="url(#star-glow)" opacity="0.8" />
                        <circle cx="50%" cy="30%" r="1.5" opacity="0.4" />
                        <circle cx="75%" cy="80%" r="2" filter="url(#star-glow)" opacity="0.9" />
                        <circle cx="85%" cy="15%" r="1" opacity="0.5" />
                        <circle cx="95%" cy="50%" r="1.5" opacity="0.7" />
                        <circle cx="35%" cy="10%" r="2" filter="url(#star-glow)" opacity="0.6" />
                        <circle cx="15%" cy="85%" r="1.5" opacity="0.8" />
                        <circle cx="65%" cy="45%" r="1" opacity="0.5" />
                        <circle cx="45%" cy="90%" r="1" opacity="0.6" />
                        <circle cx="80%" cy="35%" r="1.5" opacity="0.4" />
                        <circle cx="5%" cy="40%" r="2" filter="url(#star-glow)" opacity="0.7" />
                        <circle cx="60%" cy="15%" r="1" opacity="0.5" />
                        <circle cx="90%" cy="90%" r="2" filter="url(#star-glow)" opacity="0.8" />
                        <circle cx="20%" cy="35%" r="1" opacity="0.6" />
                        <circle cx="70%" cy="60%" r="1.5" opacity="0.5" />
                        <circle cx="40%" cy="75%" r="2" filter="url(#star-glow)" opacity="0.7" />
                        <circle cx="30%" cy="45%" r="1" opacity="0.3" />
                    </g>
                </svg>
            </div>


            <div className="lua-gigante absolute -top-32 -right-32 z-10"></div>

            <div className='flex flex-col items-center z-20 w-120 h-120 border-1 rounded-2xl relative shadow-xl shadow-purple-500/30 bg-[linear-gradient(0deg,rgba(45,0,89,0.5),rgba(1,0,3,0.5))] backdrop-blur-[2px]'>
                <div className="text-white text-4xl font-bjcree">Mooney</div>
                <form onSubmit={handleSubmit(loginSucesso)} className="flex flex-col items-center gap-4">
                    <div className='flex flex-row w-80 border-1 rounded-[1vw] mt-5 border-purple-500/10 bg-purple-500/10'>

                        <Mail className="text-purple-500/150 ml-2 mt-2" size={30} /> <div className="flex flex-col">
                            <label className="z-10 ml-7 text-purple-500/90 text-sm font-poppins">
                                E-mail
                            </label>
                            <input className="ml-7" type="email" placeholder='user@gmail.com' {...register("email")} />
                            {errors.email && <span className="text-red-400 text-sm">{errors.email.message}</span>}
                        </div>

                    </div>
                    <Lock className="text-purple-500/150 ml-2 mt-2" size={30} /> <div className="flex flex-col"></div>
                    <label className="z-10 text-purple-500 text-sm font-poppins">
                        senha
                    </label>
                    <input className="border-2 border-red-90" type="password" placeholder='*****' {...register("senha")} />
                    {errors.senha && <span className="text-red-400 text-sm">{errors.senha.message}</span>}

                    <button type='submit'>entrar</button>
                </form>
            </div>
        </div>
    )
}