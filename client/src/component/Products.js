import React,{ useEffect } from 'react'
import { useQuery } from '@apollo/client'
import { GET_PRODUCT } from '../GraphQl/Queries'

const Products = () => {
    const { error,loading,data } = useQuery(GET_PRODUCT);
    useEffect(()=>{
        console.log(data);
    },[data])
    return (
        <div>
            <h1>product</h1>
        </div>
    )
}

export default Products
