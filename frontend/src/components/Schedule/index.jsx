import React, {Suspense, useEffect, useState} from 'react';
import {Spinner, Table} from "react-bootstrap";
import apiClient from "../../api/";

const Schedule = ({fromDate, toDate}) => {
    const [specialists, setSpecialists] = useState([]);
    const [schedule, setSchedule] = useState({});
    useEffect(() => {
        (async () => {
            setSpecialists(await apiClient.getSpecialists());
        })();
    }, []);

    useEffect(() => {
        (async () => {
            if (fromDate && toDate) {
                setSchedule(await apiClient.getSchedule(fromDate, toDate));
            }
        })();
    }, [fromDate, toDate]);

    const header = schedule && Object.keys(schedule).map(elem => {
        const specialistCodes = specialists[elem];
        let additionalText = specialistCodes.length > 0 ? `- ${specialistCodes.join(', ')}` : '';
        return (
            <th scope="col" style={{width: 400}}>{elem + additionalText}</th>
        );
    });

    return (
        <Suspense fallback={<Spinner animation={"grow"} />}>
            <Table bordered responsive className={'mt-3'} style={{width: "200%"}}>
                <thead>
                {header}
                </thead>
            </Table>
        </Suspense>
    );
};

export default React.memo(Schedule);