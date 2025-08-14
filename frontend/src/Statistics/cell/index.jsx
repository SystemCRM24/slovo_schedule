import { useMemo } from "react";
import useStatisticsContext from "../context/provider";
import { Spinner } from "react-bootstrap";


function Cell({day, specialist}) {
    const {getDayStat} = useStatisticsContext();

    const value = useMemo(
        () => {
            let result = getDayStat(specialist, day);
            if ( result === 'loading' ) {
                result = (<Spinner animation="border" variant="success" />);
            }
            return result
        },
        [getDayStat, day, specialist]
    )

    return (<td className={'p-0'}><div>{value}</div></td>);
}

export default Cell;