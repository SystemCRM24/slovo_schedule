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

    return (
        <AppContext.Provider 
            value={{
                dates, 
                setDates,
                reloadSchedule
            }}
        >
            {children}
        </AppContext.Provider>
    );
};