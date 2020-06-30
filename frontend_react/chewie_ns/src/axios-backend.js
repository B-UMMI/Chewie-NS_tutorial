import axios from 'axios';

const instance = axios.create({
   baseURL: 'https://tutorial.chewbbaca.online/api/NS/api',
   headers: { 'Content-Type': 'application/json' },
});

export default instance;
