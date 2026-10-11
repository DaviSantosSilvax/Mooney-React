import { ToastContainer, toast } from 'react-toastify';
import { FaCheck } from "react-icons/fa";

export function ToastSucess() {
    return (
        toast.success("Login realizado com sucesso!", {
            icon: <FaCheck size={20} color="#E72727" />,
            position: "top-right",
            autoClose: 5000,
            hideProgressBar: false,
            closeOnClick: true,
            pauseOnHover: true,
            draggable: true,
            progress: undefined,
            theme: "colored",
        })
    );
}
