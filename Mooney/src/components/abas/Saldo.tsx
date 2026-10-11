import SideBar from "../global/SideBar";

export default function Saldo() {
    return (
        <div className="relative">
            <SideBar />
            <div className="bg-[linear-gradient(0deg,#2727E7_20%,#000854,rgba(43,0,84,1))] h-screen w-screen flex flex-col items-center justify-center">
                <div className="flex flex-col">
                    <h1 className="text-7xl font-bjcree font-bold text-[black] ">
                        Bem vindo ao Mooney
                    </h1>
                </div>
            </div>
        </div>
    )
}
