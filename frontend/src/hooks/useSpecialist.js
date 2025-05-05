import {useSpecialistContext} from "../contexts/Specialist/provider.jsx";
import {useAllSpecialistsContext} from "../contexts/AllSpecialists/provider.jsx";


/**
 *
 * @returns {{specialistId: Number, specialist: {name: string, departments: string[]}}}
 */
const useSpecialist = () => {
    const specialistId = useSpecialistContext();
    const specialists = useAllSpecialistsContext();
    return {specialistId: specialistId, specialist: specialists[specialistId]};
};

export default useSpecialist;