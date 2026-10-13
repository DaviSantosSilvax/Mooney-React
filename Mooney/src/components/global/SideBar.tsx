import { useNavigate } from "react-router-dom"


export default function SideBar() {
    const navigate = useNavigate()
    return (
        <div className="fixed top-0  items-center gap-10 flex flex-col border-r border-blue-500/10 bg-blue-500/20  h-screen">
            <div className="flex flex-col items-center  gap-10  mt-20">
                <img src="/assets/icons.png" className="w-20 h-20" />

                <h1 className="text-5xl font-bjcree font-bold text-[black] ">
                    Mooney
                </h1>
                <button onClick={() => navigate("/dashboard")} className="text-3xl font-bjcree font-bold text-[black] cursor-pointer ">Dashboard</button>
                <button onClick={() => navigate("/financeiro")} className="text-3xl font-bjcree font-bold text-[black] cursor-pointer ">Financeiro</button>
                <button onClick={() => navigate("/saldo")} className="text-3xl font-bjcree font-bold text-[black] cursor-pointer ">Saldo</button>
            </div>
        </div>
    )
}