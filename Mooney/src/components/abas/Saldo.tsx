import SideBar from "../global/SideBar";
import { useEffect, useState } from 'react'
import { toast } from 'react-toastify';

export default function Saldo() {
    const [listaBancos, setListaBancos] = useState<any[]>([])
    const [banco, setBanco] = useState("")
    const [transacao, setTransacao] = useState(0)
    const [novoSaldo, setNovoSaldo] = useState(0)
    const [saldo, setSaldo] = useState(0)
    useEffect(() => {
        async function buscarSaldo() {
            const resposta = await fetch("http://localhost:8000/api/saldo")
            const data = await resposta.json()
            console.log(data)
            setSaldo(data.saldo_total)
        }
        buscarSaldo()
    }, [])


    useEffect(() => {
        async function buscarBancos() {
            const resposta = await fetch("http://localhost:8000/api/bancos")
            const data = await resposta.json()
            console.log(data)
            setListaBancos(data)
        }
        buscarBancos()
    }, [])

    async function novoBanco(e: any) {
        e.preventDefault();
        console.log("Enviando banco para banco:")
        await fetch('http://localhost:8000/api/contas', {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ banco: banco, saldo_atual: novoSaldo })
        })
        setBanco("")
        toast.success("Banco adicionado com sucesso!")
        setSaldo(saldo + novoSaldo)
    }

    async function novaTransacao(e: any) {
        e.preventDefault();
        console.log("Eniando para o banco:")
        await fetch('http://localhost:8000/api/transacoes', {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ valor: transacao, descricao: "Nova transação" })
        });
        setSaldo(saldo + transacao);
        toast.success("Transação Registrada com sucesso!");
        setTransacao(0);
    }




    return (
        <div className="relative">
            <SideBar />
            <div className="bg-[linear-gradient(0deg,#2727E7_20%,#000854,rgba(43,0,84,1))] h-screen w-screen flex flex-col items-center ">


                <div className="relative top-5  flex flex-row bg-[rgba(0,0,0,0.5)] shadow-2xl shadow-white/10 rounded-2xl justify-center items-center p-10">
                    <div className="flex flex-row gap-10 items-end ">
                        <h1 className="text-6xl font-black font-orbitron text-transparent bg-clip-text bg-gradient-to-b from-white via-blue-100 to-indigo-300 drop-shadow-[0_0_25px_rgba(90,140,255,0.6)] select-none uppercase ">
                            Seu Saldo Atual
                        </h1>
                        <div className="flex flex-col items-end mt-1 bg-[rgba(0,0,0,0.5)] p-5 border border-[#4b05e483] rounded-[1vw]">
                            <h1 className="text-1xl font-bold text-[#d2e9ff] ">SALDO TOTAL:</h1>
                            <h2 className="text-6xl font-bold text-[#d2e9ff] ">R$ {saldo}</h2>
                        </div>
                    </div>
                </div>
                <div className="left-130 relative top-5 flex flex-col bg-[rgba(0,0,0,0.5)] shadow-2xl shadow-white/10 rounded-2xl justify-center items-center p-10">
                    <h1 className="text-3xl font-black font-orbitron text-transparent bg-clip-text bg-gradient-to-b from-white via-blue-100 to-indigo-300 drop-shadow-[0_0_25px_rgba(90,140,255,0.6)] select-none uppercase ">Ultimas transações</h1>
                </div>
                <div className="flex flex-row gap-10 items-end">

                    <form onSubmit={novoBanco} className="flex flex-col items-end">
                        <h1 className="text-1xl font-bold text-[#d2e9ff]">NOVO BANCO:</h1>
                        <input
                            type="text"
                            value={banco}
                            onChange={(e) => setBanco(e.target.value)}
                            placeholder="Nome do Banco"
                            className="text-black bg-white rounded-lg p-2"
                        />
                        <input
                            type="number"
                            value={novoSaldo}
                            onChange={(e) => setNovoSaldo(Number(e.target.value))}
                            placeholder="Saldo inicial"
                            className="text-black bg-white rounded-lg p-2 mt-2"
                        />
                        <button className="p-2 bg-blue-500 rounded-lg text-white mt-2" type="submit">
                            Adicionar Banco
                        </button>
                    </form>

                    <form onSubmit={novaTransacao} className="flex flex-col items-end">
                        <h1 className="text-1xl font-bold text-[#d2e9ff]">NOVA TRANSAÇÃO:</h1>
                        <input
                            type="number"
                            value={transacao}
                            onChange={(e) => setTransacao(Number(e.target.value))}
                            placeholder="Valor"
                            className="text-black bg-white rounded-lg p-2"
                        />
                        <select
                            value={banco}
                            onChange={(e) => setBanco(e.target.value)}
                            className="text-black bg-white rounded-lg p-2 mt-2"
                        >
                            <option value="">Selecione o banco</option>
                            {listaBancos.map((banco) => (
                                <option key={banco.id} value={banco.id}>
                                    {banco.banco}
                                </option>
                            ))}
                        </select>
                        <button className="p-2 bg-blue-500 rounded-lg text-white mt-2" type="submit">
                            Enviar Transação
                        </button>
                    </form>

                </div>
            </div>
        </div>
    )
}
