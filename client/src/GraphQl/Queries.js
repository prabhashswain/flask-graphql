import { gql } from '@apollo/client';

export const GET_PRODUCT = gql`
                          query{
                            products{
                                edges{
                                  node{
                                      name
                                      description
                                      price
                                      quantity
                                    }
                                  }
                                }
                             }
                        `