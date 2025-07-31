import React, { useState, useCallback } from "react";
import { AppContext } from "./context.js";

export const AppContextProvider = ({ children }) => {
    const [dates, setDates] = useState({ fromDate: undefined, toDate: undefined });

    const reloadSchedule = useCallback(
        () => {
            setDates({
                fromDate: new Date(dates.fromDate),
                toDate: new Date(dates.toDate)
            });
        },
        [dates]
    );

    const [modalWindowCount, setModalWindowCount] = useState(0);

    const increaseModalCount = () => setModalWindowCount(modalWindowCount + 1);
    const decreaseModalCount = () => setModalWindowCount(modalWindowCount - 1);

    return (
        <AppContext.Provider 
            value={{
                dates, 
                setDates,
                reloadSchedule,
                modalWindowCount,
                increaseModalCount,
                decreaseModalCount
            }}
        >
            {children}
        </AppContext.Provider>
    );
};