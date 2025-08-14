import { useMemo } from "react";
import useStatisticsContext from "../context/provider";



function Headers({specialists}) {

    const { getTotalStat } = useStatisticsContext();

    const colls = useMemo(
        () => specialists.map(
            (s) => {
                const codes = s.departments.join(', ');
                const stat = getTotalStat(s.id);
                return (
                    <th
                        scope="col"
                        style={{ minWidth: '220px', whiteSpace: 'pre-wrap' }}
                        key={`specialist_${s.id}_header`}
                    >   
                        <div className="d-flex justify-content-evenly align-items-center">
                            <span>{s.name + '\n' + codes}</span>
                            {stat !== null && <span>{stat}</span>}
                        </div>
                    </th>
                );
            }
        ),
        [specialists, getTotalStat]
    );

    return (
        <thead>
            <tr>
                <th key={'spec_header'} className="sticky-corner" scope="col" />
                {colls}
            </tr>
        </thead>
    );
}

export default Headers;