import { InMemoryCache,ApolloClient,ApolloProvider,from,HttpLink } from '@apollo/client'
import { onError } from '@apollo/client/link/error'
import Products from './component/Products'

const errorLink = onError(({ graphqlErrors,networkErrors })=>{
  if (graphqlErrors) {
    graphqlErrors.map(({ message,location,path })=>{
      alert(`graphql error ${message}`)
    })
  }
})
const link = from([
  errorLink,
  new HttpLink({uri:`http://127.0.0.1:5000/graphql`})
])

const client = new ApolloClient({
  cache: new InMemoryCache(),
  link:link
})

function App() {
  return (
    <ApolloProvider client={client} >
      <Products />
    </ApolloProvider>
  );
}

export default App;
