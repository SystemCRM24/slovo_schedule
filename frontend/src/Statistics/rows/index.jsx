import { useCallback, useMemo } from "react";
import Cell from "../cell";

function Rows({ dates, specialists }) {

    const getRow = useCallback(
        (day) => {
            const dayOfWeek = day.toLocaleString('ru-RU', { weekday: 'long' });
            const date = day.toLocaleDateString();
            return (
                <tr key={date}>
                    <th key={date + dayOfWeek} style={{ minHeight: '100px', height: 'auto' }}>
                        {dayOfWeek}<br />{date}
                    </th>
                    {specialists.map(
                        s => {
                            const key = `${day.toLocaleDateString()}_${s.id}`;
                            return <Cell key={key} day={day} specialist={s.id}/>;
                        }
                    )}
                </tr>
            );
        },
        [specialists]
    );
    
    const rows = useMemo(
        () => {
            const result = [];
            let currentDate = new Date(dates.fromDate);
            while ( currentDate <= dates.toDate ) {
                const dayOfWeek = currentDate.getDay();
                if ( dayOfWeek !== 0 && dayOfWeek !== 6) {
                    result.push(getRow(currentDate));
                }
                currentDate = new Date(currentDate);
                currentDate.setDate(currentDate.getDate() + 1);
            }
            return result;
        },
        [dates]
    );

    return (<tbody>{rows}</tbody>);
}

export default Rows;